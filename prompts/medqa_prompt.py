MEDICAL_ANSWER = (
    "Answer the following medical question correctly using the fictitious patient scenario. "
    "{outline}\n\n"
    "{question}"
    "Options: {choices}\n"
    "Return ONLY the 0 based integer index of your selected answer from the list and nothing else "
)
MED_PRIVACY_EVALUATION_CONFIDENCE_INSTRUCTION = ("You are very knowledgeable about medicine. "
                                             "Given the following question, answer how confident you are the proposed answer is correct "
                                             "on a continuous scale ranging from 0 to 100 that starts with 0 "
                                             "corresponding to 'certainly incorrect', goes through 1 - 50"
                                             " corresponding to 'possibly correct', then 51 - 99 corresponding "
                                             "to 'most likely correct', up to 100 corresponding to 'certainly correct'"
                                             " And then respond the reason why you give this score."
                                             " {format_instructions}\n\nThe question is here:"
                                            "{anonymised_text}. {question}"
                                            "The possible answer is: {answer}")