from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import Tool
from website.test_bot import text_search, csv_search

from dotenv import load_dotenv
_ = load_dotenv()

tool = TavilySearchResults(max_results=4) #increased number of results


text = Tool.from_function(
    func=text_search,
    name="text_search",
    description="use this to when customer ask about information about ephomaker for example like polici, delivery, about ephomaker, accessories atd...",

)
'''
gmail = Tool.from_function(
    func=gmail_message,
    name="gmail_message",
    description="use this tool when customer want to send email to our support.",

)'''

csv = Tool.from_function(
    func=csv_search,
    name="csv_search",
    description="use this tool when customers question is about keyboards or items. this can get information like price, sale, in stock or not, atd...",

)


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")

class Agent:

    def __init__(self, model, tools,checkpointer, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}
    
prompt = """You are a smart and helpfull assistant in firma called Epmomaker. Use the tools to answer the question.. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!
Make sure you provided customers with neccessary details
"""
question = 'which types of delivery do you have'

model = ChatOpenAI(model="gpt-4o")  #reduce inference cost
abot = Agent(model, [tool, text, csv],checkpointer=memory, system=prompt)



def ai(question, id):
    messages = [HumanMessage(content=question)]
    thread = {"configurable": {"thread_id": id}}
    for event in abot.graph.stream({"messages": messages}, thread):
        pass
    for x in event['llm']['messages'][0]:
        return x[1]       


