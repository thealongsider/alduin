"""Alduin - A minimal CLI coding agent."""

import os
from typing import Any

import anthropic
import dotenv
import rich
from rich.console import Console
from alduin.llm import call
import alduin.system_prompt as system_prompt
import alduin.schema_converter as schema_converter
import alduin.tool as tool

from alduin import theme, ui

active_tools = [tool.read_file]

tools_lookup = {t.__name__: t for t in active_tools}

def execute_tool(
    name_of_tool_to_execute: str, 
    tools_lookup_table: dict,
    args: Any, 
    console: Console,
) -> str: 
    #get the tool function to execute
    func = tools_lookup_table.get(name_of_tool_to_execute)

    if not func:
        error_msg = f"ERROR unknown tool {name_of_tool_to_execute}"
        ui.print_tool_error(
            console = console,
            name = name_of_tool_to_execute,
            error = error_msg
        )  
        return error_msg

    ui.print_tool_request(
        console = console,
        name = name_of_tool_to_execute,
        args = args
    )

    try:
        result = func(**args)
        ui.print_tool_result(
            console = console,
            name = name_of_tool_to_execute,
            result = result
        )
        return result
    except Exception as ex:
        error_msg_try = f"Error in calling tool {name_of_tool_to_execute}"
        ui.print_tool_error(
            console = console,
            name = name_of_tool_to_execute,
            error = error_msg_try
        )  
        return error_msg_try


def agent_loop(client: anthropic.Anthropic, console: Console) -> None:
    """Run the main agent loop: read input, call LLM, execute tools, repeat.

    Args:
        client: The initialized Anthropic client.
        console: The Rich Console for logging and UI.
    """

    conversation: list[dict[str, Any]] = [] # maintain the state of conversation as a list. Send it with the LLM every time we make a call

    while True:
        try:
            user_input = input("🧑‍💻 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            ui.clear_previous_line()
            ui.print_goodbye(console)
            return

        if not user_input:
            continue

        conversation.append({"role": "user", "content": user_input})

        ui.clear_previous_line()
        ui.print_user_message(console, user_input)

        while True:
            assistant_reply = call(client = client, 
                                console = console,
                                system_prompt = system_prompt.get(),
                                messages = conversation,
                                tool_schemas = schema_converter.generate_tool_schema(active_tools))

            rich.pretty.pprint(assistant_reply) # allows us to see the response. 

            conversation.append({"role": "assistant", "content": assistant_reply.content})
            tool_results = [] # to keep track of all the additional tool calls from doing a tool call

            for block in assistant_reply.content: # why is this a loop? 
                if block.type == "text":
                    ui.print_assistant_reply(console=console, 
                            text=block.text, 
                            input_tokens=assistant_reply.usage.input_tokens, 
                            output_tokens=assistant_reply.usage.output_tokens)
                elif block.type =="tool_use":
                    print(f"tool use requested for tool: {block.name} with args: {block.input}")
                    result = execute_tool(
                        block.name,
                        tools_lookup,
                        block.input,
                        console
                    )
                    tool_results.append(
                        {
                            "type":"tool_result",
                            "tool_use_id":block.id,
                            "content": result
                        }
                    )
                    
            if not tool_results: # if no more tools to call break out.
                break

            conversation.append(
                {
                    "role":"user",
                    "content": tool_results
                }
            )

            


        


def main() -> None:
    """Entry point for the Alduin CLI agent.

    Initializes console, checks API key, and starts the agent loop.
    """

    console = Console(theme=theme.ALDUIN_THEME)
    ui.print_banner(console)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        ui.print_error(console, "ANTHROPIC_API_KEY environment variable is not set.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    agent_loop(client=client, console=console)


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()
