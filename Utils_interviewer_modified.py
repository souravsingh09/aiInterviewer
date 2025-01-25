import json
from langchain_openai import ChatOpenAI
import re
import win32com.client
import pythoncom

# INSTANTIATING LLM
llm = ChatOpenAI(
    openai_api_key= "EMPTY",
    openai_api_base = "http://10.179.82.226:8010/v1",
    model_name = "./models/Meta-Llama-3.1-8B-Instruct-awq",
    temperature = 0,  
    max_tokens = 2000,
    stop_sequences=["<|eot_id|>"],
    # model_kwargs={"stop": ["<|eot_id|>"]},
)

def extract_single_json_object(jsonString: str):
    firstValue = jsonString.index("{")
    lastValue = len(jsonString) - jsonString[::-1].index("}")
    jsonString = jsonString[firstValue:lastValue]

    return jsonString

def correct_json_in_string(result: str):
    pattern = r'"([^"]*)\'\s*:'
    pattern_2 = r':\s\'([^"]*)"'
    # Substitute single quote with double quote
    modified_result = re.sub(pattern, r'"\1":', result)
    modified_result = re.sub(pattern_2, r': "\1"', modified_result)

    return modified_result
class Utils_Interviewer:

    def __init__(self):
        
        self.info = {}

    def read_json(self, unique_id):
        """
        This method will read the json file created by the create_json method
        """
        with open(f'static/scheduled_interviews/{unique_id}/data.json', 'r') as f:
            self.info = json.load(f)
        return self.info    


    def evaluate_transcript(self):
        with open('chat_history.txt') as f:
            transcript = f.readlines()

        prompt = f"""
Given the transcript of the interview below, create a json object with the questions as the key and answers given by candidate as the value.

Ignore any introduction made by the interviewee or greetings as well as concluding remarks. 

TRANSCRIPT:
{transcript}
"""

        result = llm.invoke(prompt).content
        print(result)
        json_obj_ques_ans = eval(extract_single_json_object(result))  

#         prompt = f"""
# Given the following json object consisting of question as key and answers as value for an interview, group the questions and answers based on the topics of discussion. The followup questions should be grouped under the main question. The output should be a json object with the topics as key and the questions and answers as value.

# TRANSCRIPT:
# {json_obj_ques_ans}
# """

#         result = llm.invoke(prompt).content
#         print(f"RESULT GROUPING: {result}")
#         json_obj_grouped_ques = eval(extract_single_json_object(result))

        topics_wise_interaction_vital = {}
        for topic in self.info["vital_topics"]:
            prompt=f"""
Given the following json object consisting of question as keys and answer as values for an interview, extract the questions and answers directly related to the topic: {topic}. The output should be a json object with the topic as key and the value as another json object with the relevant questions as key and their answers as value.

If there are no questions directly related to the topic return empty json. NEVER GENERATE EITHER QUESTION OR ANSWER OF YOUR OWN WILL.

Your job is only to provide a json object with the questions and answers related to the topic. DO NOT GENERATE ANY CODE.

VERY IMPORTANT: ENSURE THAT YOU ENCLOSE STRINGS BY DOUBLE QUOTES ONLY.


# TRANSCRIPT:
# {json_obj_ques_ans}
# 
"""         
            result = llm.invoke(prompt).content
            # print(result)
            json_obj_grouped_ques = eval(extract_single_json_object(correct_json_in_string(result)))
            print(f"RESULT GROUPING : {json_obj_grouped_ques}")
            topics_wise_interaction_vital.update(json_obj_grouped_ques)

        print(f"Final Dictionary: {topics_wise_interaction_vital}")

        combined_eval = ""

        scores = {}


        for topic, ques_ans in topics_wise_interaction_vital.items():
            print(f"QUES_ANSWER: {ques_ans.keys()}")
            if len(ques_ans) != 0 and list(ques_ans.keys()) != [""]:
                prompt = f"""
For the provided topic, and the questions and answers provided during interview provide a single score for the topic. The score should be based on the relevance of the questions and answers to the topic. The score should be a number between 0 and 1 or "NA" if no questions are relevant to the topic. 

Be extremely strict in your evaluation. Just mentioning something about the topic in the answer is not enough. There needs to be explanation or details provided that are relevant to the topic.

Give 0 if no relevant details or concrete explanation is provided or no elaboration is made for the claims made.

If the questions were not relevant with respect to the topic, give score as "NA".

ALWAYS ENSURE THAT FINAL OUPUT has A json object with the topic as key and the score as value.

TOPIC: { topic}
TRANSCRIPT:
{topics_wise_interaction_vital[topic]}

    """
                # print(prompt)
                result = llm.invoke(prompt).content
                print(result)
                combined_eval += result
                scores.update(eval(extract_single_json_object(result)))

        if len(scores.values()) == 0:
            vital_eval = 0
        else:
            vital_eval = sum(scores.values())/len(scores.values())

        topics_wise_interaction_good = {}
        for topic in self.info["good_to_know_topics"]:
            prompt=f"""
Given the following json object consisting of question as keys and answer as values for an interview, extract the questions and answers related to the topic: {topic}. The output should be a json object with the topic as key and the value as another json object with the questions as key and answers as value.

If there are no questions directly related to the topic return empty json. NEVER GENERATE EITHER QUESTION OR ANSWER OF YOUR OWN WILL.

Your job is only to provide a json object with the questions and answers related to the topic. DO NOT GENERATE ANY CODE.

VERY IMPORTANT: ENCLOSE KEYS AND VALUES IN JSON OBJECT ARE ENCLOSED BY SAME QUOTES.

# TRANSCRIPT:
# {json_obj_ques_ans}
# 
"""         
            result = llm.invoke(prompt).content
            
            json_obj_grouped_ques = eval(extract_single_json_object(correct_json_in_string(result)))
            
            print(f"RESULT GROUPING: {json_obj_grouped_ques}")
            topics_wise_interaction_good.update(json_obj_grouped_ques)

        print(f"Final Dictionary: {topics_wise_interaction_good}")

        combined_eval = ""

        scores = {}


        for topic, ques_ans in topics_wise_interaction_good.items():
            print(f"QUES_ANSWER: {ques_ans.keys()}")
            if len(ques_ans) != 0 and list(ques_ans.keys()) != [""]:
                prompt = f"""
For the provided topic, and the questions and answers provided during interview provide a single score for the topic. The score should be based on the relevance of the questions and answers to the topic. The score should be a number between 0 and 1. 

Be extremely strict in your evaluation. Just mentioning something about the topic in the answer is not enough. There needs to be explanation or details provided that are relevant to the topic.

Give 0 if no relevant details or concrete explanation is provided or no elaboration is made for the claims made.

ALWAYS ENSURE THAT FINAL OUPUT has A json object with the topic as key and the score as value.

TOPIC: { topic}
TRANSCRIPT:
{topics_wise_interaction_good[topic]}

    """
                # print(prompt)
                result = llm.invoke(prompt).content
                print(result)
                combined_eval += result
                scores.update(eval(extract_single_json_object(result)))

        if len(scores.values()) == 0:
            good_eval = 0
        else:
            good_eval = sum(scores.values())/len(scores.values())

        final_eval = (2*vital_eval + good_eval)/3

        combined_eval += f"\nThe final evaluation score is {final_eval}"

        return combined_eval

    def send_transcript_and_result(self, email, candidate_name, result):
        # Set up the SMTP server
        ol=win32com.client.Dispatch("outlook.application", pythoncom.CoInitialize())
        print(f"Inside send_transcript_and_result: {email}, {candidate_name}, {result}")
        newmail=ol.CreateItem(0x0)
        newmail.Subject = f"Interview Transcript and AI Evaluated Result - {candidate_name}"
        newmail.To = 'jm00885180@TechMahindra.com'
        newmail.Body = f"""Please find in attachment the transcript of the AI Interview.
        

Additionally find AI evaluated result of {candidate_name} below:


{result}
"""
        attachment_path = "D:\\Projects\\AI-Interviewer-llama3\\chat_history.txt"

        newmail.Attachments.Add(attachment_path)
        newmail.Send()

        # os.remove('D:\Projects\AI_Interviewer\chat_history.txt')

            
if __name__ == "__main__":
    utils_interviewer = Utils_Interviewer()
    utils_interviewer.read_json("tXxlfKaHKwqx8s7S")
    result = utils_interviewer.evaluate_transcript()
    # utils_interviewer.send_transcript_and_result("jobinmathewsp@outlook.com", "Jobin", result)
    print(result)