import csv
import os
import openai
import sys
import tempfile
import json
from dotenv import load_dotenv

def generate_prompt(categories, context, text, system_instruction=None):
    """
    Constructs the prompt for the LLM based on dynamic categories.
    """
    if not categories:
        categories = ["Uncategorized"]
    
    categories_str = "\n".join([f"    • {cat}" for cat in categories])
    
    default_instruction = "You are an expert text analyst. Your task is to categorize a piece of interview text into one or more relevant subthemes."
    instruction = system_instruction if system_instruction else default_instruction
    
    prompt = f"""
    {instruction}
    You will be given:
    1. Context from the interview question: {context}
    2. A response statement (the text to categorize): {text}

    Using the themes/categories below, determine which are meaningfully reflected in the statement.  
    A statement may belong to:
    • one category,  
    • multiple categories, or  
    • none — in which case return ["Uncategorized"].

    Do not guess. Only assign a category if there is clear evidence.

    -------------------------
    CATEGORIES
    -------------------------
    
    {categories_str}

    -------------------------
    OUTPUT FORMAT
    -------------------------

    Return ONLY a JSON object in this format:

    {{
    "subthemes": ["<category1>", "<category2>", ...],
    "rationale": "<2–4 sentence explanation showing why each category was selected>"
    }}

    If no category is appropriate, return:

    {{
    "subthemes": ["Uncategorized"],
    "rationale": "The statement does not match any defined indicators."
    }}

    -------------------------
    TASK INPUT
    -------------------------
    Now determine all applicable subthemes.
    """
    return prompt

def classify_text_with_llm(text, context=None, api_key=None, model="gpt-5.1", log_callback=print, categories=None, system_instruction=None):
    """
    Sends text to OpenAI GPT-5.1 for classification and returns an array of categories.
    """
    load_dotenv() # Load environment variables from .env file
    
    # Use provided API key, or fall back to env var
    openai.api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
    
    if not openai.api_key:
        error_msg = "OPENAI_API_KEY environment variable not set in .env file or environment, and no key provided."
        log_callback(error_msg)
        raise ValueError(error_msg)

    # Use default system instruction if not provided
    if not system_instruction:
        system_instruction = "You are a helpful assistant that classifies text into predefined categories."

    prompt = generate_prompt(categories, context, text, system_instruction)
    
    log_callback(f"Prompt sent to LLM: {prompt[:200]}...") # Log start of prompt
    # log_callback(f"Context variable: {context}") 
    # log_callback(f"Text variable: {text}") 

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200, 
            n=1,
            stop=None,
            temperature=0.0
        )
        
        # Extracting the content
        classification_str = response.choices[0].message.content.strip()
        
        # Attempt to parse the string as a JSON object
        llm_output = json.loads(classification_str)
        
        if not isinstance(llm_output, dict) or "subthemes" not in llm_output or "rationale" not in llm_output:
            raise ValueError("LLM response is not a valid JSON object with 'subthemes' and 'rationale'.")
            
        return llm_output
    except json.JSONDecodeError as e:
        log_callback(f"Error decoding JSON from LLM response: {e}")
        return {"subthemes": ["ERROR"], "rationale": f"JSON decoding error: {e}"}
    except Exception as e:
        log_callback(f"Error classifying text with LLM: {e}")
        return {"subthemes": ["ERROR"], "rationale": f"Classification error: {e}"}

def process_csv_with_llm(input_csv_path, api_key=None, model="gpt-5.1", log_callback=print, categories=None, system_instruction=None):
    """
    Reads a CSV file, classifies text in the first column using an LLM,
    and appends the categories to the same row in new columns.
    The original CSV file is overwritten with the updated data.
    """
    if not os.path.exists(input_csv_path):
        log_callback(f"Error: The file '{input_csv_path}' does not exist.")
        return

    # Use default categories if none provided (for safety, though UI should provide them)
    if not categories:
        categories = ["Uncategorized"] # Or load from default_settings if we imported it
        
    # Use a temporary file for writing to ensure data integrity
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8', dir=os.path.dirname(input_csv_path))
    temp_file_path = temp_file.name
    
    try:
        with open(input_csv_path, 'r', newline='', encoding='utf-8') as infile:
            csv_reader = csv.reader(infile)
            csv_writer = csv.writer(temp_file)

            header = next(csv_reader, None)
            if header:
                # Prepare new header with subtheme columns and rationale
                new_header = list(header)
                new_header.extend(categories)
                new_header.append("Rationale")
                csv_writer.writerow(new_header)
            
            interviewer_context = "(No preceding question. This may be an opening statement or introduction.)" # Initialize context for first statement
            current_source_file = None

            # Calculate total rows for logging (optional but helpful) by reading file first or just logging
            # Doing a simple read to count might be slow for huge files, so let's just process.
            
            for i, row in enumerate(csv_reader):
                if not row or len(row) < 4: # Ensure row has at least 4 columns: source_file, name, timestamp, statement
                    csv_writer.writerow(row)
                    continue

                source_file, name, timestamp, statement_text = row[0], row[1], row[2], row[3]
                if (i + 1) % 5 == 0:
                     log_callback(f"Processing row {i+1}: '{statement_text[:30]}...'")

                # Check for file change to reset context
                if source_file != current_source_file:
                    log_callback(f"New source file detected: {source_file}. Resetting context.")
                    interviewer_context = "(No preceding question. This may be an opening statement or introduction.)"
                    current_source_file = source_file

                # Check if the statement is from an interviewer based on the 'name' column
                # This could also be configurable, but for now we'll stick to strict "Interviewer*" checks 
                # or maybe just check if "Interviewer" is in the name.
                is_interviewer = "Interviewer" in name

                # Initialize subtheme scores to 0 and rationale to empty
                subtheme_scores = {subtheme: 0 for subtheme in categories}
                rationale_text = ""

                if is_interviewer:
                    interviewer_context = statement_text # Update context with the most recent interviewer statement
                    # We might want a specific column for "Interviewer" if it's in the categories list
                    if "Interviewer" in subtheme_scores:
                        subtheme_scores["Interviewer"] = 1 # Mark as interviewer
                    rationale_text = "Statement from interviewer."
                else:
                    # Classify the statement using the current interviewer context
                    llm_result = classify_text_with_llm(
                        statement_text, 
                        interviewer_context, 
                        api_key=api_key, 
                        model=model, 
                        log_callback=log_callback,
                        categories=categories,
                        system_instruction=system_instruction
                    )
                    
                    if llm_result and "subthemes" in llm_result:
                        for subtheme in llm_result["subthemes"]:
                            if subtheme in subtheme_scores:
                                subtheme_scores[subtheme] = 1
                        rationale_text = llm_result.get("rationale", "")
                    
                new_row = list(row) # Create a mutable copy of the original row
                new_row.extend([subtheme_scores[subtheme] for subtheme in categories])
                new_row.append(rationale_text)
                csv_writer.writerow(new_row)
        
        # Close the temporary file before replacing
        temp_file.close()
        # Replace the original file with the temporary one
        os.replace(temp_file_path, input_csv_path)
        log_callback(f"Successfully processed and updated '{input_csv_path}'.")

    except Exception as e:
        log_callback(f"Error processing CSV file: {e}")
        # Clean up temporary file if an error occurs
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python csv_classifier.py <input_csv_file>")
        sys.exit(1)

    input_csv = sys.argv[1]
    process_csv_with_llm(input_csv)
