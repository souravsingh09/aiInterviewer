# IMPORTS
from langchain_openai import ChatOpenAI
import PyPDF2 as pypdf
import docx
import json
from concurrent.futures import ThreadPoolExecutor
import os


# FLAG DICTIONARY OBJECT
score_tracking = {}

# INSTANTIATING LLM
llm = ChatOpenAI(
    openai_api_key= "EMPTY",
    openai_api_base = "http://10.179.82.226:8010/v1",
    model_name = "./models/Meta-Llama-3.1-8B-Instruct-awq",
    temperature = 0,  
    max_tokens = 2000,
    stop_sequences=["<|eot_id|>"],
    
    # model_kwargs={"seed": 0,
    #               "top_p":0.01},
)

# FUNCTION TO READ DOCUMENTS
def extract_text_from_doc(file):
    text = ""
    if file.endswith(".pdf"):
        
        pdf_reader = pypdf.PdfReader(file)
        # obtain the text from the pdf
        #text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    elif file.endswith(".docx"):
        doc = docx.Document(file)
        #text = ""
        for para in doc.paragraphs:
            text += para.text
    elif file.endswith(".txt"):
        #text=""
        with open(file, "r") as f:
            text = f.read()
    return text

# FUNCTION TO EXTRACT JSON OBJECT FROM LLM OUTPUT
def extract_single_json_object(jsonString: str):
    try:
        firstValue = jsonString.index("{")
        lastValue = len(jsonString) - jsonString[::-1].index("}")
        jsonString = jsonString[firstValue:lastValue]
    except:
        print(f"ERROR extract_single_json_object: {jsonString}")

    return jsonString

# FUNCTION TO EXTRACT JD RELATED INFORMATION
def extract_jd_info(jd_text):
    prompt = f"""
Extract the following information from the job description :
- job_role (Job role for which interview is being conducted.)  
- educational_qualification (Educational Qualification needed for the job role.)  
- work_experience (Minimum years needed. Return empty if no such information is provided.)
- must_have_skills (Only Skills or technology which are specifically mentioned as must have in the text provided.)
- optional_skills (Skills or any knowledge which are specifically mentioned as optional to have or good to have in the text provided.)

EXPECTED OUTPUT: Json Object with the extracted details. If any detail is not present return an empty string.

JOB DESCRIPTION:
{jd_text}
"""
    
    response = llm.invoke(prompt).content
    # print(f"response:{response}")
    # print(f"EXTRACTED: {extract_single_json_object(response)}")
    response = eval(extract_single_json_object(response))

    return response

# FUNCTION TO EXTRACT RESUME RELATED INFORMATION
def extract_resume_info(resume_text):
    prompt = f"""
Extract the following information from the job description :
- name (Name of the candidate)
- email (Email of the candidate)
- education_qualification (Education/Qualification of the candidate along with CGPA/Percentage)
- work_experience (Professional Work Experience in enterprises including time duration in years with all tasks and responsibilities carried out. Do not include projects in this field.)
- skills (Any and all tools or softwares or technical knowledge used or mentioned by the candidate anywhere in the context including in projects)
- project_tools (tools used in projects. Return empty list if none mentioned)

EXPECTED OUTPUT: Json Object with the extracted details. If any detail is not present return an empty string. Ensure all numbers, fraction are put in double quotes.

JOB DESCRIPTION:
{resume_text}
"""
    response = llm.invoke(prompt).content
    # print(f"ISSUE CAUSING RESPONSE{response}")
    response = eval(extract_single_json_object(response))

    return response

# FUNCTION TO CALCULATE QUALIFICATION SCORE
def calculateQualificationScore(jd_info, resume_info):
    #Calculating the score
    prompt = f"""
Educational qualification required for the job are {', '.join(jd_info['educational_qualification'])}
#########################
Education and other qualifications of the candidate are {', '.join(resume_info['education_qualification'])}

Score only the qualification of the candidate with the job description such as education etc between 0 and 1 in decimals. 
Be lenient while grading and even if educational degrees are similar give 1.
"""
    # print("#######################")
    print(prompt)
    # print("#######################")

    response = llm.invoke(prompt)
    print(response)

    return response.content

# FUNCTION TO CALCULATE WORK EXPERIENCE SCORE
def calculateWorkExperienceScore(jd_text, resume_text):
    # print(resume_text['work_experience'])
    work_exp = []
    for item in resume_text['work_experience']:
        if isinstance(item, dict):
            work_exp.append(str(item))
        elif isinstance(item, str):
            work_exp.append(item)
    resume_text['work_experience'] = work_exp
        
    work_experience = "of 0 years" if not resume_text['work_experience'] else ', '.join(resume_text['work_experience'])
    jd_relevant_text = f""" 
Work Experience needed for the job is {', '.join(jd_text['work_experience'])} 
Must have skills are {', '.join(jd_text['must_have_skills'])}
"""
    resume_relevant_text = f""" 
Education and other qualifications of the candidate are {', '.join(resume_text['education_qualification'])}
Work Experiences of the candidate are {work_experience}
"""
    #Calculating the score
    prompt = f"""
```{jd_relevant_text}```
#########################
```{resume_relevant_text}```

Follow the following steps to calculate the work experience score:
1. For all the experiences mentioned, determine whether they are only project, educational or non professional experiences and reject them if they are.
2. For all the remaining experiences, shortlist only those that mentioned that they utilized the needed skills.
3. Now for all the remaining relevant experiences calculate or extract the total number of months of experience by subtracting the start and end date if provided for all relevant instances and sum them all up. Take Present year as 2024 if needed for calculating experience
4. Calculate the score as a ratio of (candidate's relevant experience in months/ work experience required in months) with MAXIMUM VALUE as 1.
5. Remember that the score should have a maximum value of 1.
6. If there is no work experience mentioned, give a score of 0.
"""
    # print("#######################")
    # print(prompt)
    # print("#######################")

    response = llm.invoke(prompt)
    # print(response)

    return response.content

# FUNCTION TO IDENTIFY WHICH MUST HAVE REQUIREMENTS MATCH
def matchRequirements_ms(jd_info, resume_info):
    skills_match = {}
    if isinstance(resume_info["skills"], dict):
        skill_list = []
        for key in resume_info["skills"]:
            skill_list.extend(resume_info["skills"][key])
        resume_info["skills"] = skill_list
    print(resume_info["skills"])
    Resume_Skills = list(set(resume_info['skills'] + resume_info["project_tools"]))
    for skill in jd_info["must_have_skills"]:
        prompt = f"""
Perform the following steps:
RESUME SKILLS of the Candidate are: {Resume_Skills}
1. For the JD skill "{skill}" identify the resume skills if it is explicitly and exactly matches otherwise ignore. DO NOT CONSIDER BROADER MATCHES OR ASSUME SIGNI.
2. create only a single json object with the following structure:
{{
    "{skill}": list of exactly matched skills
}}
"""
        resp = llm.invoke(prompt).content

        prompt2 = f"""
Extract the final json from the below output. ONLY IF YOU ARE NOT ABLE TO EXTRACT THE JSON OBJECT THEN RETURN EMPTY JSON.
###OUTPUT###
{resp}
"""
        response = llm.invoke(prompt2).content
        print("$$$$$$$   OP INPUT ",response)
        try: 
            skills_match.update(json.loads(f"{extract_single_json_object(response)}"))
        except Exception as e:
            print(f"INSIDE EXCEPTION: {extract_single_json_object(response)}")
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("$$$$$$$   OP",response)

    return skills_match

# FUNCTION TO IDENTIFY WHICH OPTIONAL REQUIREMENTS MATCH
def matchRequirements_os(jd_info, resume_info):
    skills_match = {}
    if isinstance(resume_info["skills"], dict):
        skill_list = []
        for key in resume_info["skills"]:
            skill_list.extend(resume_info["skills"][key])
        resume_info["skills"] = skill_list
    print(resume_info["skills"])
    Resume_Skills = list(set(resume_info['skills'] + resume_info["project_tools"]))
    for skill in jd_info["optional_skills"]:
        prompt = f"""
Perform the following steps:
RESUME SKILLS of the Candidate are: {Resume_Skills}
1. For the JD skill "{skill}" identify the resume skills if it is explicitly and exactly matches otherwise ignore. DO NOT CONSIDER BROADER MATCHES OR ASSUME SIGNI.
2. create only a single json object with the following structure:
{{
    "{skill}": list of exactly matched skills
}}
"""
        resp = llm.invoke(prompt).content

        prompt2 = f"""
Extract the final json from the below output. ONLY IF YOU ARE NOT ABLE TO EXTRACT THE JSON OBJECT THEN RETURN EMPTY JSON.
###OUTPUT###
{resp}
"""
        response = llm.invoke(prompt2).content
        print("$$$$$$$   OS INPUT ",response)
        try: 
            skills_match.update(json.loads(f"{extract_single_json_object(response)}"))
        except Exception as e:
            print(f"INSIDE EXCEPTION: {extract_single_json_object(response)}")
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("$$$$$$$   OS",response)

    return skills_match

# FUNCTION TO EXTRACT QUALIFICATION AND WORK EXPERIENCE SCORE
def extract_qual_work_score(combined_eval: str):
    prompt = f"""
Extract the following individual scores of the candidates from the evaluation provided:
- qualification_score (Score of the qualification of the candidate with the job description such as education etc. If no such information is provided always give 0. Should be between 0 and 1)

- work_experience_score (Score of the work experience of the candidate with the job description. If no such information is provided always give 0. Should be between 0 and 1)

EXPECTED OUTPUT: Json Object with the extracted score. no need of explanations

EVALUATION:
{combined_eval}
"""
    response = llm.invoke(prompt).content
    response = eval(extract_single_json_object(response))

    return response

# FUNCTION TO OBTAIN THE FINAL SCORE
def score_jd_resume(jd_rel_info: dict, resume_rel_info: dict):
    denom = 0
    combined_eval = ""

    with ThreadPoolExecutor() as executor:
        if not score_tracking.get('work_experience'):
            t1 = executor.submit(calculateWorkExperienceScore, jd_rel_info, resume_rel_info)
        if not score_tracking.get('educational_qualification'):
            t2 = executor.submit(calculateQualificationScore, jd_rel_info, resume_rel_info)
        if not score_tracking.get('optional_skills'):
            t4 = executor.submit(matchRequirements_os, jd_rel_info, resume_rel_info)
        t3 = executor.submit(matchRequirements_ms, jd_rel_info, resume_rel_info)

        if not score_tracking.get('work_experience'):
            work_exp_eval = t1.result()
            combined_eval += f"{work_exp_eval}\n"
            denom += 4
        if not score_tracking.get('educational_qualification'):
            edu_eval = t2.result()
            combined_eval += f"{edu_eval}\n"
            denom += 1
        if not score_tracking.get('optional_skills'):
            satisfied_opt_count = 0
            req_opt_eval = t4.result()
            # print(req_opt_eval)
            for key in req_opt_eval:
                if not (len(req_opt_eval[key]) == 0):
                    satisfied_opt_count += 1
            denom += 2
        
        satisfied_must_count = 0
        req_must_eval = t3.result()
        for key in req_must_eval:
            if not (len(req_must_eval[key]) == 0):
                satisfied_must_count += 1
        denom += 4

    if combined_eval != "":
        qual_score_dict = extract_qual_work_score(combined_eval)
    else:
        qual_score_dict = {"qualification_score": 0, "work_experience_score": 0}

    if not score_tracking.get('optional_skills'):
        value=4*(satisfied_must_count/len(jd_rel_info["must_have_skills"]))+2*(satisfied_opt_count/len(jd_rel_info["optional_skills"]))
        print(f"Satisfied Opt Count {satisfied_opt_count}")
        print(f"total optional skills: {len(jd_rel_info['optional_skills'])}")
    else:
        value=4*(satisfied_must_count/len(jd_rel_info["must_have_skills"]))

    print(f"Satisfied Must Count{satisfied_must_count}")
    print(f"Total must have skills: {len(jd_rel_info['must_have_skills'])}")
    print(f"Qualification Score: {qual_score_dict['qualification_score']}")
    print(f"Work Experience Score: {qual_score_dict['work_experience_score']}")
    print(f"Value: {value}")
    print("denom", denom)
    final_result = (qual_score_dict['qualification_score'] + 4*min(qual_score_dict['work_experience_score'], 1) + value)/denom*100

    return final_result, qual_score_dict['qualification_score'], qual_score_dict['work_experience_score'], value

# FUNCTION TO EVALUATE THE JD AND RESUME MATCHING
def evaluate_jd_resume_match(resume_path: str, jd_path: str):
    jd_text = ""
    resume_text = ""
    with ThreadPoolExecutor() as executor:
        thread1 = executor.submit(extract_text_from_doc, jd_path)
        thread2 = executor.submit(extract_text_from_doc, resume_path)
        jd_text = thread1.result()
        resume_text = thread2.result()
    
    jd_rel_info = {}
    resume_rel_info = {}
    with ThreadPoolExecutor() as executor:
        thread3 = executor.submit(extract_jd_info, jd_text)
        thread4 = executor.submit(extract_resume_info, resume_text)
        jd_rel_info = thread3.result()
        resume_rel_info = thread4.result()

    if not jd_rel_info['work_experience']:
        score_tracking["work_experience"] = "NA"
    if not jd_rel_info['educational_qualification']:
        score_tracking["educational_qualification"] = "NA"
    if not jd_rel_info['optional_skills']:
        score_tracking["optional_skills"] = "NA"

    name = resume_rel_info["name"]
    final_ans, qualification_score, work_exp_score, skills_score = score_jd_resume(jd_rel_info, resume_rel_info)

    return jd_rel_info, resume_rel_info, final_ans, qualification_score, work_exp_score, skills_score, name

if __name__ =="__main__":
    # jd_folder = "JDs"
    # resume_folder = "Resumes"
    # for jd_filename in os.listdir(jd_folder):
    #     for resume_filename in os.listdir(resume_folder):
    #         try: 
    #             score_tracking = {}
    #             jd_path = os.path.join(jd_folder, jd_filename)
    #             resume_path = os.path.join(resume_folder, resume_filename)
    #             print(f"JD: {jd_path}")
    #             print(f"Resume: {resume_path}")
    #             jd_rel_info, resume_rel_info, final_ans, qualification_score, work_exp_score, skills_score, name = evaluate_jd_resume_match(resume_path, jd_path)
    #             print(f"Final Score: {final_ans}")
    #             print(f"Name: {name}")
    #             print(f"Qualification Score: {qualification_score}")
    #             print(f"Work Experience Score: {work_exp_score}")
    #             print(f"Skills Score: {skills_score}")
    #         except:
    #             print("ERROR HAD OCCURRED")
    #             score_tracking = {}
    #             jd_path = os.path.join(jd_folder, jd_filename)
    #             resume_path = os.path.join(resume_folder, resume_filename)
    #             print(f"JD: {jd_path}")
    #             print(f"Resume: {resume_path}")
    #             jd_rel_info, resume_rel_info, final_ans, qualification_score, work_exp_score, skills_score, name = evaluate_jd_resume_match(resume_path, jd_path)
    #             print(f"Final Score: {final_ans}")
    #             print(f"Name: {name}")
    #             print(f"Qualification Score: {qualification_score}")
    #             print(f"Work Experience Score: {work_exp_score}")
    #             print(f"Skills Score: {skills_score}")

    jd_path = "JDs\\JD - ML.pdf"
    resume_path = "Resumes\\Sakshi's Resume_data_analyst.pdf"

    jd_rel_info, resume_rel_info, final_ans, qualification_score, work_exp_score, skills_score, name = evaluate_jd_resume_match(resume_path, jd_path)
    print(f"Final Score: {final_ans}")
    print(f"Name: {name}")
    print(f"Qualification Score: {qualification_score}")
    print(f"Work Experience Score: {work_exp_score}")
    print(f"Skills Score: {skills_score}")