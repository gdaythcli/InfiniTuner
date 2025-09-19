from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import os


def process_log_chunks(chunks, agent):
    all_summaries = []
    
    for idx, chunk in enumerate(chunks):
        print(f"Processing chunk {idx + 1}/{len(chunks)}...")
        
        # Define the prompt for this chunk
        prompt = f"""
        Please analyze the following chunk of a log file (chunk {idx + 1} of {len(chunks)}):
        {chunk.page_content}
        
        Analyze it and summarize useful performance information, such as throughput, latency metrics.
        If you choose to write Python code for analysis, generate the code first and then execute it using the available Python REPL tool.
        If you choose to analyze it directly, do so.
        Then print out the summary of the findings.
        
        Thought: What should I do next?
        Action: (Choose 'python_repl' if using Python, otherwise proceed with analysis.)
        Action Input: (Provide the input or Python script.)
        """
        print("Prompt for chunk:")
        print(prompt)
        
        # Run the agent with the prompt
        chunk_summary = agent.run(prompt)
        print(f"Summary for chunk {idx + 1}:")
        print(chunk_summary)
        all_summaries.append(chunk_summary)
    
    # Combine all summaries
    final_prompt = f"""
    Here are the summaries of chunks of the log file:
    {all_summaries}

    Please give me a comprehensive summary report for the log file. 
    I want to know the overall concrete performance metrics numbers, such as throughput, latency metrics, and resource usage.
    Then print out the summary report.
    """
    final_summary = agent.run(final_prompt)
    print("Final Summary of the Log File:")
    print(final_summary)
    return final_summary

# def summary_benchmark(outputs):
#     '''
#     Function to summarize the benchmark results
#     '''
#     python_repl = PythonREPL()

#     repl_tool = Tool(
#         name="python_repl",
#         description=(
#             "A Python shell. Use this to execute Python scripts. "
#             "Input should be a valid Python script. "
#             "If you want to see the output of a value, you should print it out with `print(...)`."
#         ),
#         func=python_repl.run,
#     )

#     documents = [Document(page_content=outputs)]
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=0)
#     texts = text_splitter.split_documents(documents)
#     embeddings = OpenAIEmbeddings()
#     vector_store = FAISS.from_documents(texts, embeddings)

#     llm = ChatOpenAI(model_name="gpt-4o")

#     # Initialize the agent with the REPL tool
#     agent = initialize_agent(
#         tools=[repl_tool],
#         llm=llm,
#         agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Ensure correct agent type
#         verbose=True,
#         handle_parsing_errors=True,
#     )

#     key_words = ["performance metrics", "resource usage"]
#     query = " ".join(key_words)  # Combine keywords into a single string query
#     relevant_chunks = vector_store.similarity_search(query, k=3)
#     results = process_log_chunks(relevant_chunks, agent)
#     return results

def split_string_by_length(s, max_length):
    """Split a string into chunks with a maximum length, keeping whole lines when possible.

    If a single line exceeds ``max_length``, the line is further sliced into sub-strings.

    Args:
        s (str): Input string that may contain newline characters.
        max_length (int): Maximum length of each chunk; must be greater than 0.

    Returns:
        List[str]: List of chunks whose lengths do not exceed ``max_length``.
    """
    if max_length <= 0:
        raise ValueError("max_length must be greater than 0")
    
    result = []
    current_chunk = ""
    
    # Use splitlines(keepends=True) to preserve newline characters within each line
    for line in s.splitlines(keepends=True):
        # Split the line further if it individually exceeds max_length
        if len(line) > max_length:
            # Flush the current chunk if it already has content
            if current_chunk:
                result.append(current_chunk)
                current_chunk = ""
            # Emit slices of the long line, each no longer than max_length
            for i in range(0, len(line), max_length):
                piece = line[i:i+max_length]
                result.append(piece)
        else:
            # Check whether appending the line keeps the chunk within max_length
            if len(current_chunk) + len(line) <= max_length:
                current_chunk += line
            else:
                # Otherwise flush the chunk and start a new one with the current line
                if current_chunk:
                    result.append(current_chunk)
                current_chunk = line

    if current_chunk:
        result.append(current_chunk)
        
    return result

def process_first_log_file(log_content, agent, log_path):
    """
    Processes the first log file:
    - Analyzes each chunk separately.
    - Generates a Python script for each chunk.
    - Extracts performance metrics for each chunk.
    - After processing all chunks, asks the LLM to generate a single Python script 
      that can process the entire log file at once.
    """
    
    # Step 1: Split the log into chunks
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=0)
    # chunks = text_splitter.split_text(log_content)
    

    chunks = split_string_by_length(log_content, 10000)
    print(f"First log file split into {len(chunks)} chunks.")

    chunk_scripts = []

    # Step 2: Process each chunk separately
    for idx, chunk in enumerate(chunks):
        print(f"Processing chunk {idx + 1}/{len(chunks)}...")

        # Step 2.1: Ask LLM to analyze log format for this chunk
        format_analysis_prompt_raw = f"""
        Help me to analyze a log file from a Data System.
        Please analyze the structure of the following log chunk:

        {chunk}

        First identify the format, if this chunk contains key performance metrics (e.g., throughput, latency, resource usage),
        please suggest how to extract them programmatically in python script, run the script using the Python REPL tool. 
        Or you can extract performance metrics directly.
        If this chunk does not contain any key performance metrics, please say "No key performance metrics found".
        Then give me the python script or indication of no key performance metrics or performance metrics directly.
        
        Thought: What should I do next?
        Action: (Choose 'python_repl' if using Python, otherwise proceed with analysis.)


        NOTE: If your script fails to run, please analyze the error and correct it. DO NOT GIVE PARTIAL PATCHES. ALWAYS GIVE FULL NEW SCRIPT.
        """
        format_analysis_prompt = f"""
        You need to analyze log files from a Data System and extract key performance metrics (e.g., throughput, latency, resource usage) for further tuning. As the log file may be extremely large, I will split it into multiple chunks. Each chunk is enclosed within <log></log> tags.

        For each provided log chunk, please follow these steps:

        1. Check the log chunk format to determine whether it contains any key performance metrics.
        2. If key performance metrics are found, write a complete, runnable Python script that extracts these metrics.
        3. Run the script using the Python REPL tool to verify that it works correctly. If the script fails, analyze the error and provide a complete, corrected version of the script (do not provide partial patches).
        4. If the script runs successfully, check its output to ensure it contains the expected performance metrics with VALID values.
        5. Compare the output with the original log chunk to ensure that the script has correctly extracted the performance metrics.
        6. If the log chunk does not contain any key performance metrics, return a Python script that does nothing (e.g., a simple empty script).

        Now log chunks begin:
        <log>
        {chunk}
        </log>
        """
        # print(agent.agent.llm_chain.prompt.template)
        
        # log_format_script = agent.invoke(format_analysis_prompt).content
        log_format_script = agent.invoke({"input": format_analysis_prompt})
        print(log_format_script.keys())
        log_format_script = log_format_script['output']

        print(f"Log Format Analysis for Chunk {idx + 1}:\n", log_format_script)
        chunk_scripts.append(log_format_script)

    

    if len(chunk_scripts) > 1:

    # Step 3: Ask LLM to generate a final script for processing the entire log
        final_script_prompt = f"""
        Your task is to merge several Python scripts for processing log data into one optimized script that can handle the entire log file at once.

        We have analyzed different segments of a log file, and for each segment, we generated one of the following:
        - A Python script for processing that segment,
        - An indication that no key performance metrics were found, or
        - A summary of performance metrics.

        Please complete the following steps: 
        1. Review the provided Python scripts or indications for each log segment.
        2. Combine these scripts into a single, optimized Python script capable of processing the entire log file in one go.
        3. Verify that the final script includes all key performance metrics from every segment.
        4. The original log file is located at {log_path}. Run the script using the Python REPL tool. Please print out the Python REPL tool results.
        5. If your script fails to run, please analyze the error and correct it. DO NOT GIVE PARTIAL PATCHES. ALWAYS GIVE FULL NEW SCRIPT.
        6. Please return the final Python script.

        Below are the individual scripts or indications:
        {''.join(["<script>\n" + script + "\n</script>\n" for script in chunk_scripts])}

        """

        final_script_prompt_raw = f"""
        We have analyzed multiple chunks of a log file and generated Python scripts or indications of no key performance metrics or performance metrics for each chunk.

        Here are the scripts for individual chunks or indication of no key performance metrics or performance metrics:
        {chunk_scripts}

        Now, based on these information, generate a **single optimized Python script**
        that can process the entire log file at once, instead of processing chunk by chunk.
        Run the script using the Python REPL tool. Please print out the Python REPL tool results.
        Please give me the final python script.

        NOTE: If your script fails to run, please analyze the error and correct it. DO NOT GIVE PARTIAL PATCHES. ALWAYS GIVE FULL NEW SCRIPT.
        """

        # final_python_script = agent.invoke(final_script_prompt).content
        final_python_script = agent.invoke({"input": final_script_prompt})
        # print(final_python_script.keys())
        final_python_script = final_python_script['output']
        print("Final Python Script for Full Log Processing:\n", final_python_script)
    else:
        final_python_script = chunk_scripts[0]
        print("Only one script generated, using it directly.")
        print("Final Python Script for Full Log Processing:\n", final_python_script)
        # If only one script is generated, we can use it directly without further processing.
        # This assumes that the single script is already optimized for the entire log file.
    return final_python_script  # Save this to reuse for future logs

    # This script should:
    # - Read the log file line by line.
    # - Identify and extract all relevant performance metrics.
    # - Compute aggregates/statistics efficiently.
    # - Output the structured performance results.

def process_additional_log_file(log_path, agent, final_python_script):
    """
    Processes additional log files using the final optimized Python script
    generated from the first log file.
    """
    
    execution_prompt = f"""
    We have already generated a Python script that can process the entire log file efficiently.

    Here is the script:
    {final_python_script}


    Now, correct and run this script on the log file located at {log_path} by Python REPL tool.
    Or analysis it directly by loading this log file using Python REPL tool.

    NOTE: If your script fails to run, please analyze the error and correct it. DO NOT GIVE PARTIAL PATCHES. ALWAYS GIVE FULL NEW SCRIPT.


    Please return the extracted performance metrics.
    """
    
    execution_result = agent.run(execution_prompt)
    print("Execution Result for New Log File:\n", execution_result)
    
    return execution_result

def summary_benchmark(outputs):
    '''
    Function to summarize the benchmark results
    '''

    if os.path.exists('./search/log_scripts.py'):
        from search.log_scripts import extract_metrics
        results = extract_metrics(outputs)
        print("Extracted Metrics:\n", results)
        return results
    else:
        print("log_scripts.py not found. We will create it.")

    python_repl = PythonREPL()

    repl_tool = Tool(
        name="python_repl",
        description=(
            "A Python shell. Use this to execute Python scripts. "
            "Input should be a valid Python script. "
            "If you want to see the output of a value, you should print it out with `print(...)`."
        ),
        func=python_repl.run,
    )

    # llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
    llm = ChatOpenAI(model_name="o3-mini", reasoning_effort="low")


    # Initialize the agent with the REPL tool
    # agent = initialize_agent(
    #     tools=[repl_tool],
    #     llm=llm,
    #     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Ensure correct agent type
    #     verbose=True,
    #     handle_parsing_errors=True,
    # )
    from langchain_core.prompts import PromptTemplate

    template = '''Answer the following questions as best you can. You have access to the following tools:

    {tools}

    STRICTLY Use the following format(DO NOT MODIFY THE FORMAT):

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: 
    the input to the action(e.g.```python\nprint("Hello World")\n```)
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: 
    the final answer to the original input question

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}'''

    prompt = PromptTemplate.from_template(template)
    from langchain.agents import AgentExecutor, create_react_agent
    agent = create_react_agent(llm, [repl_tool], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[repl_tool], handle_parsing_errors=True, verbose = True)

    # results_scripts = process_first_log_file(outputs, agent, '/home/alice/LLM-Trace-Auto-Tuning/search/log.txt')
    results_scripts = process_first_log_file(outputs, agent_executor, '/home/alice/LLM-Trace-Auto-Tuning/search/log.txt')
    print("Results Scripts:\n", results_scripts)

    # TODO save the log_scripts.py to reuse
    # results = save_log_scripts('/home/alice/LLM-Trace-Auto-Tuning/search/log_scripts.py', agent_executor, results_scripts)
    # results = process_additional_log_file('./search/log.txt', agent_executor, results_scripts)
    # print("Results:\n", results)

    
    return results

if __name__ == "__main__":
    # Example usage
    with open('./search/log.txt', 'r') as file:
        log_content = file.read()
    
    summary_benchmark(log_content)
