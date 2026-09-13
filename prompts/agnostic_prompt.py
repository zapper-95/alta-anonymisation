REWRITING_INSTRUCTION_AUX_LINKING_UTILITY = (
    "You are restoring utility to an anonymised document. The document has been "
    "previously anonymised against several adversaries who each hold a disjoint "
    "subset of auxiliary information from the original document, and the current "
    "privacy level is above the required threshold. Your task is to gently reintroduce "
    "useful information from the original text where this can be done without "
    "pushing privacy back below the threshold.\n\n"

    "The conclusions the original document establishes are given below. They were "
    "determined from the original text before any anonymisation and do not change "
    "as the document is transformed. Your task is to gently re-establish them: a "
    "reader of the rewritten document should be able to draw the same conclusions "
    "as a reader of the original.\n\n"
    "{conclusions}\n\n"

    "Below is the original document, the current anonymised document, and "
    "synthesised feedback from across all the adversaries explaining which content "
    "still contributes to re-identification risk. Rewrite the current anonymised "
    "document, reintroducing content from the original where the following hold:\n"
    "- The reintroduced content moves the document closer to supporting the "
    "conclusions listed above.\n"
    "- The reintroduced content is not itself among the material the adversaries "
    "flagged as identifying.\n"
    "- The reintroduced content does not, in combination with other retained "
    "content, restore a distinctive pattern the adversaries could exploit. "
    "Reintroducing two details individually may be safe, but their combination may "
    "recreate an identifying signal.\n\n"

    "Content in the current document that is already supporting its conclusion "
    "does not need to be changed, even if it is more vague than the original. It "
    "is already carrying its utility, and returning to the original value would "
    "restore precise information about the person for no gain.\n\n"

    "Only revise a previous anonymisation when you can justify that the reintroduced "
    "information adds meaningful utility and does not restore identifying signal "
    "the adversaries could rely upon.\n\n"

    "Verge on the side of introducing too little information back to the document over too much. "

    "{format_instructions}\n\n"

    "The original document is:\n{input_text}\n\n"
    "The current anonymised document (with suggestion appended) is:\n{prev_rewriting}\n\n"
    "The synthesised adversary feedback is:\n{reflection_privacy}"
)
REWRITING_INSTRUCTION_AUX_LINKING_PRIVACY = (
    "You are anonymising a document by coarsening. An adversary with auxiliary "
    "information about the person has provided feedback on which details in the "
    "current text still enable re-identification. Your task is to rewrite the "
    "document, by generalising the details the adversary flagged so "
    "they no longer narrow the population to this individual.\n\n"

    "Every detail the adversary identifies as distinctive must be transformed. "
    "Coarsen by generalising the detail to a broader true statement, or remove it "
    "entirely if any generalisation broad enough to be non-identifying would convey no useful information. "
    "Assume the adversary can hold any background knowledge that could reasonably be obtained about "
    "a person.\n\n"

    "Leave unflagged details at their original level of specificity to preserve utility. "
    "Exception: if the adversary missed a direct identifier in the document, coarsen or remove it anyway.\n\n"

    "Coarsening only removes information; it never invents or replaces it. Do "
    "not substitute a flagged value for a different specific value ('my husband "
    "and I' → 'my wife and I' is a fabrication, not a coarsening). Valid moves "
    "are generalisation ('my husband and I' → 'my partner and I').\n\n"

    "Consider conjunctions carefully: two individually innocuous details may "
    "jointly re-identify. If the adversary's feedback flags a combination "
    "rather than a single detail, coarsen enough of the combination to break "
    "the pattern.\n\n"

    "Preserve the original text's structure, ordering, and register. The output "
    "must read as an ordinary document. Do not signal that the document has "
    "been anonymised, and do not introduce placeholders, redaction markers, or "
    "generic phrasing such as \"an individual\" where a specific detail would "
    "be natural.\n\n"

    "{format_instructions}\n\n"

    "The current document is:\n{prev_rewriting}\n\n"
    "Thhe adversary feedback is:\n{reflection_privacy}"
)

FACT_EXTRACTION_INSTRUCTION_1 = (
    "Extract every atomic fact from the document below. An atomic fact is a single, "
    "self-contained statement asserting one piece of information — either explicitly "
    "stated in the document or directly inferable from it. Facts should be concise, "
    "non-overlapping, and verifiable as true or false against the document.\n\n"
    "CRITICAL RULE — one identifier per fact:\n"
    "Each fact must contain exactly ONE identifying detail. Never combine multiple "
    "identifiers (name, date, place, nationality, occupation, etc.) into a single "
    "fact. If a sentence says 'John Smith was born on 5 March 1990 in Berlin', that "
    "must become separate facts: one for the name, one for the birth date, one for "
    "the birth place. A fact like 'The person is John Smith, born in 1990' violates "
    "this rule because it bundles a name and a date — split them.\n\n"
    "CRITICAL RULE — person reference:\n"
    "The person's name appears in the document. In your extracted facts, you must "
    "refer to this person as 'the person' throughout. The person's name may appear "
    "in AT MOST ONE fact (the fact that introduces their name as a piece of "
    "information). Every other fact must use 'the person' instead of the name. "
    "Do not paraphrase the name (e.g. surname only, initials, 'Mr X') — use 'the "
    "person'. This rule is mandatory because facts will be evaluated independently "
    "and any name reference would leak identity beyond the single name fact.\n\n"
    "If the document contains no extractable atomic facts, respond with an empty list.\n\n"
    "{format_instructions}\n\n"
    "Document:\n{input_text}"
)

AUX_CONFIDENCE_SCORING_INSTRUCTION = (
    "You are an investigator. You hold a list of auxiliary information about a person "
    "and have access to a single anonymised document. You do not know for certain "
    "whether this person is present in the dataset.\n\n"

    "Your task: rate how confident you are that the anonymised document corresponds to "
    "the person described by the auxiliary information. You must choose exactly one of the "
    "following values. Do not pick any number that is not on this list:\n"
    "    0  = certain it is NOT the same person\n"
    "   10  = extremely unlikely to be the same person\n"
    "   20  = very unlikely\n"
    "   30  = unlikely\n"
    "   40  = slightly unlikely\n"
    "   50  = genuinely uncertain; evidence is balanced\n"
    "   60  = slightly likely\n"
    "   70  = likely\n"
    "   80  = very likely\n"
    "   90  = extremely likely\n"
    "  100  = certain it IS the same person\n\n"

    "First, reason step by step about how well the auxiliary information matches the "
    "document: note specific points of agreement, points of tension, and how distinctive "
    "any matching details are (a shared rare detail is much stronger evidence than a shared "
    "common one). Then state which single value from the list above best reflects your "
    "confidence. Finally, on a new line, output only that integer and nothing else.\n\n"


    "Remember this is one of many anonymised documents in the dataset. Even if all your background information remains plausible, your confidence should not be high unless" \
    " the document matches very well and on pieces of information that are rare or specific to this person.\n"

    "{format_instructions}\n"
    "Auxiliary information:\n{aux_info}\n\n"
    "Anonymised document:\n{prev_rewriting}\n"
)



FACT_TRANSFORMATION_UTILITY_INSTRUCTION = (
    "You are restoring utility to an anonymised document. The document has been "
    "previously anonymised against several adversaries who have a disjoint subset of auxiliary information from the original document, and the current "
    "privacy level is above the required threshold. Your task is to reintroduce useful "
    "information from the original text where this can be done without pushing privacy "
    "back below the threshold.\n\n"

    "The conclusions the original document establishes are given below. They were "
    "determined from the original text before any anonymisation and do not change as the "
    "document is transformed. Your task is to gently re-establish them: a reader of the current "
    "document should be able to draw the same conclusions as a reader of the original.\n\n"
    "{conclusions}\n\n"

    "Below is a complete list of atomic facts from the original document, the corresponding facts "
    "from the current anonymised document, and synthesised feedback from across all the adversaries explaining "
    "which facts still contribute to re-identification risk.\n\n"
    "For EACH fact in the current document, choose exactly one transformation that best "
    "restores content while keeping the document anonymous:\n"
    "- undo(n): reverse the last n transformations applied to the fact. Use this when the fact has been unnecessarily coarsened or perturbed and we can move closer in truth to the original fact without enabling re-identification. If n is greater than the number of transformations applied to the fact, then restore the original fact. Use the smallest n that re-establishes the conclusion: a fact coarsened twice may only need one step back to convey its meaning again, and the second step returns identifying information for nothing.\n"
    "- restore: reintroduce a fact that was previously deleted. Use this when the semantic content of the fact is no longer identifying given the other facts in the current document. "
    "- identity: keep the current version as-is, whether that means a distorted value or an absence. Use this for facts that were flagged by the adversaries as identifying, or where reversing the previous transformation would push privacy back below the threshold.\n\n"

    "A fact whose current value still supports its conclusion does not need reversing, even "
    "if that value is false. It is already carrying its utility, and stepping it back would "
    "return true information about the person for no gain.\n\n"
    
    "Only reverse a previous transformation when you can justify that reintroducing the information adds meaningful utility and does not restore the identifying signal the adversaries relied on.\n"

    "Consider conjunctions carefully: reintroducing two facts individually may be safe, "
    "but their combination may restore a distinctive pattern the adversaries could exploit.\n"
    "{format_instructions}\n\n"

    "For each fact in the original document, pick a transformation to apply to the corresponding fact in the current document."
    "If it is deleted in the current document and you don't want to restore it, then choose identity. If it is deleted in the current document and you want to restore it, then choose restore."
    "Otherwise the transformation will be applied to the corresponding fact in the current document."

    "The facts from the original document are:\n{original_facts}\n\n"
    "The transformation history for each fact is:\n{fact_history}\n\n"
    "The facts from the current anonymised document are:\n{current_facts}\n\n"

    "The synthesised adversary feedback is:\n{reflection_privacy}"
)

FACT_TRANSFORMATION_INSTRUCTION = (
    "You are anonymising a document against an adversary who has auxiliary information "
    "about the person and is trying to re-identify them. Below is a list of atomic facts "
    "extracted from the text, and a summary of feedback from several adversaries on which "
    "information most allowed them to link their background information to this "
    "document.\n\n"

    "First, write 6-7 lines of reasoning about which information in the text requires "
    "transformation based upon how re-identifying it is. Then, write each fact alongside "
    "your chosen transformation and chosen strength.\n\n"

    "Perturbation should fall on the details that are identifying but not crucial to the "
    "overall picture: the specifics that narrow the population without carrying the core "
    "meaning of the document. Names, places, dates, institutions, incidental circumstances "
    "and precise values that nothing depends on are where the anonymisation should be "
    "concentrated, and perturbing them costs the document little, because a reader draws "
    "the same overall picture from a false specific as from a true one. Look for these "
    "first and transform them hardest. Where an important part of the document is supported "
    "by several independent facts, you can perturb one of them and the overall picture "
    "still follows from the rest; only where it rests on a single fact must that fact be "
    "treated cautiously.\n\n"

    "For EACH fact, choose exactly one transformation and one transformation strength that "
    "best reduces the document's re-identification risk while keeping it plausible, "
    "consistent and readable:\n\n"

    "Transformations\n\n"

    "coarsen: replace the fact with a strictly more general version (e.g. 'a lightning bolt "
    "scar on his forehead' -> 'a scar on his head').\n"
    "WHEN TO APPLY:\n"
    "1. Apply to proper nouns for something that is public and verifiable (e.g. a named "
    "person, place, or organisation).\n"
    "2. Facts that have several facts that depend upon them. For example, several facts may "
    "depend on a person playing a particular sport (teammates, dates of events, teams "
    "played for), and an alternative would require altering these facts too.\n"
    "3. Facts that exist in a small equivalence class (e.g. attendees of a particular niche "
    "event).\n"

    "perturb: replace the fact with an equally specific but different fact at the same "
    "level of abstraction (e.g. 'he had a pet dog' -> 'he had a pet cat'; a named city for "
    "a different named city). The replacement must be FALSE for this person: if the "
    "perturbed fact would still be true given the original, you have rephrased rather than "
    "perturbed, and the anonymisation has gained nothing ('completed successfully' -> "
    "'concluded effectively' is a rephrasing). Do not add or remove qualifiers that change "
    "severity, scale or significance; adding 'minor' to an injury understates it rather "
    "than replacing it.\n"
    "WHEN TO APPLY:\n"
    "1. Where suitable alternatives exist that are realistic and consistent with the other "
    "facts in the document, and where the fact is not fundamental to the document's "
    "meaning.\n"
    "2. For facts where not many other facts depend upon them. For example, if someone were "
    "from Greece, and the document talks about places, events and people from Greece, then "
    "perturbation is preferred for these dependent facts rather than the independent one. "
    "This is to prevent inconsistencies being created. If other facts do depend on a "
    "perturbed one, you must also perturb these so that they can remain consistent.\n"
    "3. Proper nouns where it is not publicly verifiable, for example non-famous names of "
    "people or events.\n\n"

    "specialise: keep the true fact but add an invented refinement at a finer level of "
    "detail (e.g. 'he liked dogs' -> 'he liked poodles'). The refinement must not restore "
    "the original information or narrow the description back towards the true person.\n"
    "WHEN TO APPLY:\n"
    "1. Where a fact is likely to exist in an adversary's background knowledge at finer "
    "granularity than the document states, and the space of possible refinements is "
    "large.\n\n"

    "delete: remove the fact entirely.\n"
    "WHEN TO APPLY:\n"
    "1. The fact contradicts one or more of the other facts in the document (side with the "
    "interpretation with the fewest contradictions, and choose facts from the other side to "
    "be deleted).\n"
    "2. The fact seems unrelated, irrelevant, insignificant or out of place in the context "
    "of the other facts.\n"
    "3. No amount of coarsening or perturbation could ever stop this fact from being "
    "re-identifying, or several previous transformations have failed to prevent "
    "re-identification.\n\n"

    "identity: leave the fact unchanged.\n"
    "WHEN TO APPLY:\n"
    "1. The fact carries little re-identification risk.\n"
    "2. No adversary relied on this fact for re-identification.\n"
    "Identity is NOT available for any fact containing a proper noun or naming a person, "
    "place, organisation or role, even where the same entity appears unchanged elsewhere in "
    "the document. Nor is it available for a fact the adversaries named, however "
    "unremarkable it looks on its own.\n\n"

    "Transformation strengths\n\n"

    "low: For coarsening, remove only minor qualifying detail or move one hypernym step "
    "(e.g. 'a red 1967 convertible' -> 'a red convertible'). For perturbation, for "
    "categorical information move to a sibling: a different member of the same narrow "
    "subcategory (e.g. a market town in one county for a market town in a nearby county). "
    "For numerical, move to adjacent values that fall in the same category (e.g. an "
    "elevated temperature for another elevated temperature; a tall person at 6ft 2in for "
    "another tall person at 6ft 3in or 6ft 1in).\n"
    "WHEN TO APPLY: Low strength should be applied to facts that are similar to their "
    "original versions but are barely or not mentioned at all in the adversary's feedback. "
    "They have the potential to be re-identifying due to their uniqueness.\n\n"

    "medium: For coarsening, remove most qualifying details or move several taxonomic "
    "levels (e.g. 'a red 1967 convertible' -> 'a car'). For perturbation, move categories "
    "to a cousin: the same broad category but a different subcategory, region, or era (e.g. "
    "a city in one country for a city in a neighbouring country). For numeric quantities "
    "retain the general direction or magnitude but make it more or less extreme (e.g. an "
    "elevated temperature for a more elevated or a slightly elevated temperature; a tall "
    "person at 6ft 2in for a slightly taller person at 6ft 4in or a person at 6ft). The "
    "general category the numeric value falls in should be identical to the original.\n"
    "WHEN TO APPLY: Apply a medium strength transformation to typical re-identifying facts "
    "noted by the adversary.\n\n"

    "high: For coarsening, keep only the core category (e.g. 'a red 1967 convertible' -> 'a "
    "vehicle'). For perturbation, move to a distant relative: the same type of thing, "
    "maximally different while remaining plausible given this person's other information "
    "(e.g. a city in one country for a city on a different continent). For numeric "
    "quantities this should be large changes that reach the boundaries of adjacent grouped "
    "values (e.g. an elevated temperature to a borderline elevated or borderline extreme "
    "temperature; a tall person at 6ft 2in for a very tall person at 6ft 6in, or an average "
    "height person at 5ft 10in). Before choosing high, check what other facts must change "
    "with it to stay consistent.\n"
    "WHEN TO APPLY: Apply a high strength transformation ONLY where a fact has already been "
    "transformed and continues to be re-identifying, OR where the adversary indicates very "
    "directly a large amount of re-identification risk from this fact.\n\n"

    "DEFINITIONS AND RULES\n\n"

    "A fact is identifying if it is rare; if few people in the plausible population it "
    "describes would share it. Rarity is a property of the information itself, not of its "
    "surface form: a fact can be identifying without containing any proper noun, and a "
    "proper noun can be harmless if it is common. When judging if a fact is identifying, "
    "consider how many people it could equally describe and how identifying it would be if "
    "known to an adversary. Distinctive phrasing is itself a fact, since wording carried "
    "over from the original document can identify the source text even when its content is "
    "generic.\n\n"

    "A fact is 're-identifying' if it is both identifying AND matches the adversary's "
    "auxiliary information. A fact can be identifying and NOT match the adversary's "
    "auxiliary information due to previous transformations, for example a perturbed name. "
    "Such facts DO NOT require transformation even if they appear identifying, since the "
    "adversary cannot link to them. Focus on facts that are both identifying and can be "
    "matched with the adversary's auxiliary information.\n\n"

    "Judge conjunctions as well as single facts. 'A chess grandmaster who is also a "
    "stand-up comedian and known for his bright red glasses' has three common elements and "
    "a rare intersection, and where a conjunction is distinctive you must transform at "
    "least one of its elements to break it. Substituting particulars does not by itself "
    "break a conjunction: if the roles, the sequence of events and the relationships "
    "between people stay the same, the shape of the situation survives every individual "
    "replacement and remains just as identifying. Ask what the document is a story about; "
    "if that is still recoverable, change one of the elements that makes it that story "
    "rather than another surface detail.\n\n"

    "Where several facts refer to the same entity, a person, place, organisation or role, "
    "transform them together. Choosing identity for one while perturbing another leaves the "
    "document describing two entities where there was one, which reads as incoherent and "
    "marks the text as altered.\n\n"

    "Each current fact is listed with the values it has already held, oldest first. Use "
    "that trajectory. Never return a fact to a value it has already had, and never to the "
    "original value or to a different term denoting the same thing; check your chosen value "
    "against the listed values before committing to it. Where a fact has already been "
    "transformed and the feedback still flags it, escalate rather than repeat: move further "
    "within the same category, or move to coarsening or deletion. Never re-apply an "
    "operation at the same or lower strength than one that has already failed, and do not "
    "specialise a fact you previously coarsened, which returns the detail you just "
    "removed.\n\n"

    "Be critical about what information is truly identifying, as this may change as the "
    "document becomes more anonymised.\n\n"

    "All transformations will be applied to the current document's facts.\n\n"

    "The facts from the original document are:\n{original_facts}\n\n"
    "The facts from the current document, to which your transformations will be applied, "
    "each followed by the values it has already held:\n{current_facts}\n\n"
    "The summary of the adversaries' most recent feedback linking auxiliary information to "
    "this document is the following. You should follow its guidance closely but transform "
    "clear violations of privacy from the original facts it doesn't flag:\n"
    "{reflection_privacy}\n\n"

    "{format_instructions}"
)


FACT_REWRITING_INSTRUCTION = (
    "You are producing transformed versions of facts for an anonymised document. Below is "
    "a list of facts, each paired with a transformation and a strength to apply. Apply each "
    "transformation at its assigned strength and return the resulting transformed fact.\n\n"

    "Before producing any transformed facts, write a short planning paragraph. Plan the "
    "choices that must stay consistent across facts before you commit to any of them: "
    "decide upon and write the names used for entities that recur across multiple facts and "
    "what single transformed value each will take; whether any perturbed dates, ages and "
    "durations remain arithmetically consistent with each other and with retained facts; "
    "and, for public entities, which real replacement of the same type, domain and era you "
    "will use. Also identify any distinctive conjunctions, sequences of events or "
    "relationships that must be broken by the assigned transformations rather than "
    "preserved through surface-level substitutions. Then output each transformed fact, "
    "following your plan.\n\n"

    "Transformation meanings:\n"
    "- coarsen: state a strictly more general version of the fact "
    "(e.g. 'a lightning bolt scar on his forehead' -> 'a scar on his head').\n"
    "- perturb: state a different but equally specific fact at the same level of "
    "abstraction. Make the fabricated detail realistic and consistent with an ordinary "
    "document, but shifted away from the true identifying fact "
    "(e.g. 'he liked cats' -> 'he liked dogs'). The replacement must be false for this "
    "person and must not merely rephrase the original fact.\n"
    "- specialise: keep the true fact but add an invented refinement at a finer level of "
    "detail (e.g. 'he liked dogs' -> 'he liked poodles'). The refinement must not come from "
    "the original document, restore the original information, or narrow the description "
    "back towards the true person. It must be plausible for this person and should be "
    "picked from a large space of alternatives so it is unlikely to match the truth by "
    "chance. The underlying general fact must remain true as stated.\n"
    "- delete: output nothing for this fact. The fact will be removed from the document.\n"
    "- identity: return the fact exactly as given, unchanged.\n\n"

    "Strength meanings:\n"
    "- low: For coarsening, remove only minor qualifying detail or move one hypernym step "
    "(e.g. 'a red 1967 convertible' -> 'a red convertible'). For perturbation, for "
    "categorical information move to a sibling: a different member of the same narrow "
    "subcategory, such as a market town in one county for a market town in a nearby county. "
    "For numerical information, move to adjacent values that fall in the same category, "
    "such as an elevated temperature for another elevated temperature, or a tall person at "
    "6ft 2in for another tall person at 6ft 3in or 6ft 1in.\n"
    "- medium: For coarsening, remove most qualifying details or move several taxonomic "
    "levels (e.g. 'a red 1967 convertible' -> 'a car'). For perturbation, move to a cousin: "
    "the same broad category but a different subcategory, region or era, such as a city in "
    "one country for a city in a neighbouring country. For numerical quantities, retain "
    "the general direction or magnitude but make it more or less extreme. The general "
    "category the numeric value falls in should be identical to the original.\n"
    "- high: For coarsening, keep only the core category "
    "(e.g. 'a red 1967 convertible' -> 'a vehicle'). For perturbation, move to a distant "
    "relative: the same type of thing, maximally different while remaining plausible given "
    "this person's other information, such as a city in one country for a city on a "
    "different continent. For numerical quantities, make a large change that reaches the "
    "boundaries of adjacent grouped values while remaining plausible. Before applying a "
    "high-strength transformation, check what other facts must change with it to stay "
    "consistent.\n\n"

    "Rules for transformed values:\n"
    "- The perturbed value must be FALSE for this person, not the same fact in different "
    "words. If your value would still be true given the fact you were handed, you have "
    "rephrased rather than perturbed and the anonymisation has gained nothing ('completed "
    "successfully' -> 'concluded effectively' is a rephrasing, not a perturbation).\n"
    "- Each current fact is listed with the values it has already held, oldest first. Use "
    "that trajectory. Never return a fact to any of those values, to the original value, or "
    "to a different term denoting the same thing; check your value against the listed "
    "values before committing to it.\n"
    "- Where a fact has already been transformed and the feedback still flags it, the "
    "assigned transformation should move it further rather than repeat a failed value. "
    "Never reproduce an earlier value, and do not restore detail that a previous "
    "coarsening removed.\n"
    "- Keep the same qualifiers when perturbing. Do not add or drop words that change "
    "severity, scale or significance: calling an injury 'minor' when the fact did not "
    "understates it rather than replacing it, and softening in this way leaves the true "
    "severity recoverable.\n"
    "- Numbers and dates must be changed according to the assigned strength. For low "
    "strength, use an adjacent value that remains in the same category. For medium "
    "strength, retain the general direction or magnitude but make the value more or less "
    "extreme while keeping it in the same general category. For high strength, make a large "
    "change that reaches the boundary of an adjacent grouped value while remaining "
    "plausible. In every case, the value must be genuinely different and must not reproduce "
    "a value the fact has already held.\n"
    "- Where the fact being perturbed contains a public, verifiable entity, such as a "
    "well-known person, institution, competition or event, the replacement must be a real "
    "entity of the same type, domain and era; never an invented one, and never one that "
    "contradicts common world knowledge. Do not place a person in a league that does not "
    "exist in their sport, or have them interact with a public figure outside that figure's "
    "lifetime. Invented entities are acceptable only for private facts such as relatives, "
    "local businesses or personal events.\n"
    "- Perturbed lifestyle details must cohere with the role, activities and circumstances "
    "the other facts describe.\n"
    "- A specialised refinement must not restore the original information or narrow the "
    "description back towards the true person. It must preserve the underlying general "
    "fact while selecting a plausible refinement from many possible alternatives.\n\n"

    "Each transformed fact must read as a plain, confident, true statement. Never indicate "
    "that a fact is fabricated, altered, a decoy or a placeholder. Keep each transformed "
    "fact atomic and self-contained, following the basic phrasing of the current fact. "
    "However, where distinctive wording may itself identify the source document, replace "
    "it with plain equivalent wording rather than carrying it over unchanged, unless the "
    "assigned transformation is identity.\n\n"

    "Judge conjunctions as well as single facts. Several individually common details may "
    "form a rare and identifying intersection. Where the assigned transformations target "
    "one element of such a conjunction, rewrite it so that the conjunction is genuinely "
    "broken. Substituting names or other particulars does not by itself break a conjunction "
    "if the roles, sequence of events and relationships between people remain the same. Do "
    "not accidentally recreate the same identifying story through different surface "
    "details.\n\n"

    "Transformations accumulate: every value you produce becomes part of the document's "
    "ground truth for all subsequent facts. Once an entity has been transformed, every "
    "later fact referencing the same entity must use the transformed value, and dependent "
    "facts must remain consistent with it. Derived quantities must match transformed base "
    "values, such as ages matching perturbed dates; events must fall within perturbed time "
    "ranges; and related entities must share transformed identifiers, such as shared names "
    "across a family or organisation. Never transform the same underlying entity to two "
    "different values in different facts.\n\n"

    "Where several facts refer to the same entity, person, place, organisation or role, "
    "transform them together. Returning one reference unchanged while perturbing another "
    "leaves the document describing two entities where there was one, which reads as "
    "incoherent and marks the text as altered.\n\n"

    "Some facts in the document are being left unchanged and are listed separately below. "
    "You are not rewriting those, but they remain in the document, so your transformed "
    "values must stay consistent with them. If an entity you are transforming also appears "
    "in an unchanged fact, do not silently give the same underlying entity two different "
    "values. The assigned transformations should already have grouped all references to the "
    "same entity. If they do not, preserve document coherence and identify the conflict in "
    "the planning paragraph rather than inventing a second entity.\n\n"

    "For example:\n"
    "'The organisation is called Northgate Ltd' (perturb, medium) -> "
    "'The organisation is called Ashfield Ltd'\n"
    "'Northgate's headquarters are in Leeds' (perturb, medium) -> "
    "'Ashfield's headquarters are in Leeds'\n\n"

    "Another example:\n"
    "'He went to university with Prince William' (identity) -> "
    "'He went to university with Prince William'\n"
    "'He was born in 1982' (perturb, low) -> 'He was born in 1981'\n"
    "The chosen date must remain realistic: a date that made him too young or too old to "
    "have attended university with Prince William would contradict the retained fact. A "
    "consistent choice is an adjacent year in the same general category that keeps the "
    "retained fact possible.\n\n"

    "Be critical about whether a transformed fact still matches the adversary's auxiliary "
    "information. A fact may remain identifying in isolation but cease to be re-identifying "
    "once it no longer matches that information. Do not reintroduce details from the "
    "original fact or from previous values merely because they make the rewritten statement "
    "sound more natural.\n\n"

    "{format_instructions}\n\n"

    "The current facts and their assigned transformations and strengths, which you shall "
    "apply, each accompanied by the values it has already held:\n"
    "{fact_transformations}\n\n"

    "Facts that are being left unchanged, for consistency only, which you must NOT "
    "output:\n"
    "{unchanged_facts}\n\n"

    "The summary of the adversaries' most recent feedback linking auxiliary information "
    "to this document is the following. Use it to avoid preserving or recreating the "
    "information that most enabled re-identification:\n"
    "{reflection_privacy}"
)



FACT_TRANSFORMATION_INSTRUCTION_CONCLUSIONS = (
    "You are anonymising a document against an adversary who has auxiliary information "
    "about the person and is trying to re-identify them. Below is a list of atomic facts "
    "extracted from the text, and a summary of feedback from several adversaries on which "
    "information most allowed them to link their background information to this "
    "document.\n\n"

    "The conclusions the original document establishes are given below. They were "
    "determined from the original text before any anonymisation and do not change as the "
    "document is transformed. Keep them in view as you choose: a reader of the anonymised "
    "document should still be able to draw them, so a transformation that leaves the "
    "document supporting a different conclusion, or none, has cost more than one that only "
    "removes a detail.\n\n"
    "{conclusions}\n\n"

    "First, write 6-7 lines of reasoning about which information in the text requires "
    "transformation based upon how re-identifying it is, and which facts carry each "
    "conclusion. Then, write each fact alongside your chosen transformation and chosen "
    "strength.\n\n"

    "Perturbation should fall on the details that are identifying but not crucial to the "
    "overall picture: the specifics that narrow the population without carrying any "
    "conclusion. Names, places, dates, institutions, incidental circumstances and precise "
    "values that nothing depends on are where the anonymisation should be concentrated, and "
    "perturbing them costs the document nothing, because a reader draws the same "
    "conclusions from a false specific as from a true one. Look for these first and "
    "transform them hardest. Where a conclusion is supported by several independent facts, "
    "you can perturb one of them and the conclusion still follows from the rest; only where "
    "it rests on a single fact must that fact be left true.\n\n"

    "For EACH fact, choose exactly one transformation and one transformation strength that "
    "best reduces the document's re-identification risk while keeping it plausible, "
    "consistent and readable:\n\n"

    "Transformations\n\n"

    "coarsen: replace the fact with a strictly more general version (e.g. 'a lightning bolt "
    "scar on his forehead' -> 'a scar on his head').\n"
    "WHEN TO APPLY:\n"
    "1. Apply to proper nouns for something that is public and verifiable (e.g. a named "
    "person, place, or organisation).\n"
    "2. Facts that have several facts that depend upon them. For example, several facts may "
    "depend on a person playing a particular sport (teammates, dates of events, teams "
    "played for), and an alternative would require altering these facts too.\n"
    "3. Facts that exist in a small equivalence class (e.g. attendees of a particular niche "
    "event).\n"

    "perturb: replace the fact with an equally specific but different fact at the same "
    "level of abstraction (e.g. 'he had a pet dog' -> 'he had a pet cat'; a named city for "
    "a different named city). The replacement must be FALSE for this person: if the "
    "perturbed fact would still be true given the original, you have rephrased rather than "
    "perturbed, and the anonymisation has gained nothing ('completed successfully' -> "
    "'concluded effectively' is a rephrasing). Do not add or remove qualifiers that change "
    "severity, scale or significance; adding 'minor' to an injury understates it rather "
    "than replacing it.\n"
    "WHEN TO APPLY:\n"
    "1. Where suitable alternatives exist that are realistic and consistent with the other "
    "facts in the document, and where the fact is not fundamental to the document's "
    "meaning.\n"
    "2. For facts where not many other facts depend upon them. For example, if someone were "
    "from Greece, and the document talks about places, events and people from Greece, then "
    "perturbation is preferred for these dependent facts rather than the independent one. "
    "This is to prevent inconsistencies being created. If other facts do depend on a "
    "perturbed one, you must also perturb these so that they can remain consistent.\n"
    "3. Proper nouns where it is not publicly verifiable, for example non-famous names of "
    "people or events.\n\n"

    "specialise: keep the true fact but add an invented refinement at a finer level of "
    "detail (e.g. 'he liked dogs' -> 'he liked poodles'). The refinement must not restore "
    "the original information or narrow the description back towards the true person.\n"
    "WHEN TO APPLY:\n"
    "1. Where a fact is likely to exist in an adversary's background knowledge at finer "
    "granularity than the document states, and the space of possible refinements is "
    "large.\n\n"

    "delete: remove the fact entirely.\n"
    "WHEN TO APPLY:\n"
    "1. The fact contradicts one or more of the other facts in the document (side with the "
    "interpretation with the fewest contradictions, and choose facts from the other side to "
    "be deleted).\n"
    "2. The fact seems unrelated, irrelevant, insignificant or out of place in the context "
    "of the other facts.\n"
    "3. No amount of coarsening or perturbation could ever stop this fact from being "
    "re-identifying, or several previous transformations have failed to prevent "
    "re-identification.\n\n"

    "identity: leave the fact unchanged.\n"
    "WHEN TO APPLY:\n"
    "1. The fact carries little re-identification risk.\n"
    "2. No adversary relied on this fact for re-identification.\n"
    "Identity is NOT available for any fact containing a proper noun or naming a person, "
    "place, organisation or role, even where the same entity appears unchanged elsewhere in "
    "the document. Nor is it available for a fact the adversaries named, however "
    "unremarkable it looks on its own.\n\n"

    "Transformation strengths\n\n"

    "low: For coarsening, remove only minor qualifying detail or move one hypernym step "
    "(e.g. 'a red 1967 convertible' -> 'a red convertible'). For perturbation, for "
    "categorical information move to a sibling: a different member of the same narrow "
    "subcategory (e.g. a market town in one county for a market town in a nearby county). "
    "For numerical, move to adjacent values that fall in the same category (e.g. an "
    "elevated temperature for another elevated temperature; a tall person at 6ft 2in for "
    "another tall person at 6ft 3in or 6ft 1in).\n"
    "WHEN TO APPLY: Low strength should be applied to facts that are similar to their "
    "original versions but are barely or not mentioned at all in the adversary's feedback. "
    "They have the potential to be re-identifying due to their uniqueness.\n\n"

    "medium: For coarsening, remove most qualifying details or move several taxonomic "
    "levels (e.g. 'a red 1967 convertible' -> 'a car'). For perturbation, move categories "
    "to a cousin: the same broad category but a different subcategory, region, or era (e.g. "
    "a city in one country for a city in a neighbouring country). For numeric quantities "
    "retain the general direction or magnitude but make it more or less extreme (e.g. an "
    "elevated temperature for a more elevated or a slightly elevated temperature; a tall "
    "person at 6ft 2in for a slightly taller person at 6ft 4in or a person at 6ft). The "
    "general category the numeric value falls in should be identical to the original.\n"
    "WHEN TO APPLY: Apply a medium strength transformation to typical re-identifying facts "
    "noted by the adversary.\n\n"

    "high: For coarsening, keep only the core category (e.g. 'a red 1967 convertible' -> 'a "
    "vehicle'). For perturbation, move to a distant relative: the same type of thing, "
    "maximally different while remaining plausible given this person's other information "
    "(e.g. a city in one country for a city on a different continent). For numeric "
    "quantities this should be large changes that reach the boundaries of adjacent grouped "
    "values (e.g. an elevated temperature to a borderline elevated or borderline extreme "
    "temperature; a tall person at 6ft 2in for a very tall person at 6ft 6in, or an average "
    "height person at 5ft 10in). Before choosing high, check what other facts must change "
    "with it to stay consistent.\n"
    "WHEN TO APPLY: Apply a high strength transformation ONLY where a fact has already been "
    "transformed and continues to be re-identifying, OR where the adversary indicates very "
    "directly a large amount of re-identification risk from this fact.\n\n"

    "DEFINITIONS AND RULES\n\n"

    "A fact is identifying if it is rare; if few people in the plausible population it "
    "describes would share it. Rarity is a property of the information itself, not of its "
    "surface form: a fact can be identifying without containing any proper noun, and a "
    "proper noun can be harmless if it is common. When judging if a fact is identifying, "
    "consider how many people it could equally describe and how identifying it would be if "
    "known to an adversary. Distinctive phrasing is itself a fact, since wording carried "
    "over from the original document can identify the source text even when its content is "
    "generic.\n\n"

    "A fact is 're-identifying' if it is both identifying AND matches the adversary's "
    "auxiliary information. A fact can be identifying and NOT match the adversary's "
    "auxiliary information due to previous transformations, for example a perturbed name. "
    "Such facts DO NOT require transformation even if they appear identifying, since the "
    "adversary cannot link to them. Focus on facts that are both identifying and can be "
    "matched with the adversary's auxiliary information.\n\n"

    "Judge conjunctions as well as single facts. 'A chess grandmaster who is also a "
    "stand-up comedian and known for his bright red glasses' has three common elements and "
    "a rare intersection, and where a conjunction is distinctive you must transform at "
    "least one of its elements to break it. Substituting particulars does not by itself "
    "break a conjunction: if the roles, the sequence of events and the relationships "
    "between people stay the same, the shape of the situation survives every individual "
    "replacement and remains just as identifying. Ask what the document is a story about; "
    "if that is still recoverable, change one of the elements that makes it that story "
    "rather than another surface detail.\n\n"

    "Where several facts refer to the same entity, a person, place, organisation or role, "
    "transform them together. Choosing identity for one while perturbing another leaves the "
    "document describing two entities where there was one, which reads as incoherent and "
    "marks the text as altered.\n\n"

    "Each current fact is listed with the values it has already held, oldest first. Use "
    "that trajectory. Never return a fact to a value it has already had, and never to the "
    "original value or to a different term denoting the same thing; check your chosen value "
    "against the listed values before committing to it. Where a fact has already been "
    "transformed and the feedback still flags it, escalate rather than repeat: move further "
    "within the same category, or move to coarsening or deletion. Never re-apply an "
    "operation at the same or lower strength than one that has already failed, and do not "
    "specialise a fact you previously coarsened, which returns the detail you just "
    "removed.\n\n"

    "Be critical about what information is truly identifying, as this may change as the "
    "document becomes more anonymised.\n\n"

    "All transformations will be applied to the current document's facts.\n\n"

    "The facts from the original document are:\n{original_facts}\n\n"
    "The facts from the current document, to which your transformations will be applied, "
    "each followed by the values it has already held:\n{current_facts}\n\n"
    "The summary of the adversaries' most recent feedback linking auxiliary information to "
    "this document is the following. You should follow its guidance closely but transform "
    "clear violations of privacy from the original facts it doesn't flag:\n"
    "{reflection_privacy}\n\n"

    "{format_instructions}"
)


FACT_REWRITING_INSTRUCTION_CONCLUSIONS = (
    "You are producing transformed versions of facts for an anonymised document. Below is "
    "a list of facts, each paired with a transformation and a strength to apply. Apply each "
    "transformation at its assigned strength and return the resulting transformed fact.\n\n"

    "The conclusions the original document establishes are given below. They were "
    "determined from the original text before any anonymisation and do not change as the "
    "document is transformed. Keep them in view while rewriting the facts: a reader of the "
    "anonymised document should still be able to draw them. Do not produce a transformed "
    "fact that leaves the document supporting a different conclusion, or none, where a "
    "plausible transformation can preserve it.\n\n"
    "{conclusions}\n\n"

    "Before producing any transformed facts, write a short planning paragraph. Plan the "
    "choices that must stay consistent across facts before you commit to any of them: "
    "decide upon and write the names used for entities that recur across multiple facts and "
    "what single transformed value each will take; whether any perturbed dates, ages and "
    "durations remain arithmetically consistent with each other and with retained facts; "
    "which facts carry each conclusion; and, for public entities, which real replacement "
    "of the same type, domain and era you will use. Also identify any distinctive "
    "conjunctions, sequences of events or relationships that must be broken by the assigned "
    "transformations rather than preserved through surface-level substitutions. Then "
    "output each transformed fact, following your plan.\n\n"

    "Transformation meanings:\n"
    "- coarsen: state a strictly more general version of the fact "
    "(e.g. 'a lightning bolt scar on his forehead' -> 'a scar on his head').\n"
    "- perturb: state a different but equally specific fact at the same level of "
    "abstraction. Make the fabricated detail realistic and consistent with an ordinary "
    "document, but shifted away from the true identifying fact "
    "(e.g. 'he liked cats' -> 'he liked dogs'). The replacement must be false for this "
    "person and must not merely rephrase the original fact.\n"
    "- specialise: keep the true fact but add an invented refinement at a finer level of "
    "detail (e.g. 'he liked dogs' -> 'he liked poodles'). The refinement must not come from "
    "the original document, restore the original information, or narrow the description "
    "back towards the true person. It must be plausible for this person and should be "
    "picked from a large space of alternatives so it is unlikely to match the truth by "
    "chance. The underlying general fact must remain true as stated.\n"
    "- delete: output nothing for this fact. The fact will be removed from the document.\n"
    "- identity: return the fact exactly as given, unchanged.\n\n"

    "Strength meanings:\n"
    "- low: For coarsening, remove only minor qualifying detail or move one hypernym step "
    "(e.g. 'a red 1967 convertible' -> 'a red convertible'). For perturbation, for "
    "categorical information move to a sibling: a different member of the same narrow "
    "subcategory, such as a market town in one county for a market town in a nearby county. "
    "For numerical information, move to adjacent values that fall in the same category, "
    "such as an elevated temperature for another elevated temperature, or a tall person at "
    "6ft 2in for another tall person at 6ft 3in or 6ft 1in.\n"
    "- medium: For coarsening, remove most qualifying details or move several taxonomic "
    "levels (e.g. 'a red 1967 convertible' -> 'a car'). For perturbation, move to a cousin: "
    "the same broad category but a different subcategory, region or era, such as a city in "
    "one country for a city in a neighbouring country. For numerical quantities, retain "
    "the general direction or magnitude but make it more or less extreme. The general "
    "category the numeric value falls in should be identical to the original.\n"
    "- high: For coarsening, keep only the core category "
    "(e.g. 'a red 1967 convertible' -> 'a vehicle'). For perturbation, move to a distant "
    "relative: the same type of thing, maximally different while remaining plausible given "
    "this person's other information, such as a city in one country for a city on a "
    "different continent. For numerical quantities, make a large change that reaches the "
    "boundaries of adjacent grouped values while remaining plausible. Before applying a "
    "high-strength transformation, check what other facts must change with it to stay "
    "consistent.\n\n"

    "Rules for transformed values:\n"
    "- The perturbed value must be FALSE for this person, not the same fact in different "
    "words. If your value would still be true given the fact you were handed, you have "
    "rephrased rather than perturbed and the anonymisation has gained nothing ('completed "
    "successfully' -> 'concluded effectively' is a rephrasing, not a perturbation).\n"
    "- Each current fact is listed with the values it has already held, oldest first. Use "
    "that trajectory. Never return a fact to any of those values, to the original value, or "
    "to a different term denoting the same thing; check your value against the listed "
    "values before committing to it.\n"
    "- Where a fact has already been transformed and the feedback still flags it, the "
    "assigned transformation should move it further rather than repeat a failed value. "
    "Never reproduce an earlier value, and do not restore detail that a previous "
    "coarsening removed.\n"
    "- Keep the same qualifiers when perturbing. Do not add or drop words that change "
    "severity, scale or significance: calling an injury 'minor' when the fact did not "
    "understates it rather than replacing it, and softening in this way leaves the true "
    "severity recoverable.\n"
    "- Numbers and dates must be changed according to the assigned strength. For low "
    "strength, use an adjacent value that remains in the same category. For medium "
    "strength, retain the general direction or magnitude but make the value more or less "
    "extreme while keeping it in the same general category. For high strength, make a large "
    "change that reaches the boundary of an adjacent grouped value while remaining "
    "plausible. In every case, the value must be genuinely different and must not reproduce "
    "a value the fact has already held.\n"
    "- Where the fact being perturbed contains a public, verifiable entity, such as a "
    "well-known person, institution, competition or event, the replacement must be a real "
    "entity of the same type, domain and era; never an invented one, and never one that "
    "contradicts common world knowledge. Do not place a person in a league that does not "
    "exist in their sport, or have them interact with a public figure outside that figure's "
    "lifetime. Invented entities are acceptable only for private facts such as relatives, "
    "local businesses or personal events.\n"
    "- Perturbed lifestyle details must cohere with the role, activities and circumstances "
    "the other facts describe.\n"
    "- A specialised refinement must not restore the original information or narrow the "
    "description back towards the true person. It must preserve the underlying general "
    "fact while selecting a plausible refinement from many possible alternatives.\n\n"

    "Each transformed fact must read as a plain, confident, true statement. Never indicate "
    "that a fact is fabricated, altered, a decoy or a placeholder. Keep each transformed "
    "fact atomic and self-contained, following the basic phrasing of the current fact. "
    "However, where distinctive wording may itself identify the source document, replace "
    "it with plain equivalent wording rather than carrying it over unchanged, unless the "
    "assigned transformation is identity.\n\n"

    "Judge conjunctions as well as single facts. Several individually common details may "
    "form a rare and identifying intersection. Where the assigned transformations target "
    "one element of such a conjunction, rewrite it so that the conjunction is genuinely "
    "broken. Substituting names or other particulars does not by itself break a conjunction "
    "if the roles, sequence of events and relationships between people remain the same. Do "
    "not accidentally recreate the same identifying story through different surface "
    "details.\n\n"

    "Transformations accumulate: every value you produce becomes part of the document's "
    "ground truth for all subsequent facts. Once an entity has been transformed, every "
    "later fact referencing the same entity must use the transformed value, and dependent "
    "facts must remain consistent with it. Derived quantities must match transformed base "
    "values, such as ages matching perturbed dates; events must fall within perturbed time "
    "ranges; and related entities must share transformed identifiers, such as shared names "
    "across a family or organisation. Never transform the same underlying entity to two "
    "different values in different facts.\n\n"

    "Where several facts refer to the same entity, person, place, organisation or role, "
    "transform them together. Returning one reference unchanged while perturbing another "
    "leaves the document describing two entities where there was one, which reads as "
    "incoherent and marks the text as altered.\n\n"

    "Some facts in the document are being left unchanged and are listed separately below. "
    "You are not rewriting those, but they remain in the document, so your transformed "
    "values must stay consistent with them. If an entity you are transforming also appears "
    "in an unchanged fact, do not silently give the same underlying entity two different "
    "values. The assigned transformations should already have grouped all references to the "
    "same entity. If they do not, preserve document coherence and identify the conflict in "
    "the planning paragraph rather than inventing a second entity.\n\n"

    "For example:\n"
    "'The organisation is called Northgate Ltd' (perturb, medium) -> "
    "'The organisation is called Ashfield Ltd'\n"
    "'Northgate's headquarters are in Leeds' (perturb, medium) -> "
    "'Ashfield's headquarters are in Leeds'\n\n"

    "Another example:\n"
    "'He went to university with Prince William' (identity) -> "
    "'He went to university with Prince William'\n"
    "'He was born in 1982' (perturb, low) -> 'He was born in 1981'\n"
    "The chosen date must remain realistic: a date that made him too young or too old to "
    "have attended university with Prince William would contradict the retained fact. A "
    "consistent choice is an adjacent year in the same general category that keeps the "
    "retained fact possible.\n\n"

    "Be critical about whether a transformed fact still matches the adversary's auxiliary "
    "information. A fact may remain identifying in isolation but cease to be re-identifying "
    "once it no longer matches that information. Do not reintroduce details from the "
    "original fact or from previous values merely because they make the rewritten statement "
    "sound more natural.\n\n"

    "{format_instructions}\n\n"

    "The current facts and their assigned transformations and strengths, which you shall "
    "apply, each accompanied by the values it has already held:\n"
    "{fact_transformations}\n\n"

    "Facts that are being left unchanged, for consistency only, which you must NOT "
    "output:\n"
    "{unchanged_facts}\n\n"

    "The summary of the adversaries' most recent feedback linking auxiliary information "
    "to this document is the following. Use it to avoid preserving or recreating the "
    "information that most enabled re-identification:\n"
    "{reflection_privacy}"
)



DOCUMENT_REWRITING_INSTRUCTION = (
    "Write a document using the facts below."
    "It should not read as a list of facts, but naturally flow together, as if a normal document. "
    "Write the document using the facts in the order they are presented. Do include multiple facts in the same sentence if approriate and they join nicely"
    "Do NOT add narrative flourish, dramatic phrasing, or evaluative descriptions "
    "(e.g. 'dynamic', 'illustrious', 'landmark', 'pivotal', or any evaluative descriptor) "
    "The finished text must read as an ordinary, true document. Never indicate that "
    "any fact is fictional, altered, or uncertain; state everything plainly. Keep the "
    "text internally consistent; if two facts would clash, phrase around the conflict "
    "using only what is given. Output only the document prose, with no headers, "
    "labels, or commentary.\n\n"

    "{format_instructions}\n\n"
    "Facts to write the document from:\n{distorted_facts}"
)

DOCUMENT_REWRITING_ORIGINAL_REFERENCE_INSTRUCTION = (
    "Write a document using the facts below.\n\n"

    "Style: match the tone and register of the reference text below EXACTLY. Use the "
    "same kind of sentences, the same level of formality, the same directness. If the "
    "reference is plain and factual, your output is plain and factual. Do NOT add "
    "narrative flourish, dramatic phrasing, or evaluative descriptions "
    "(e.g. 'dynamic', 'illustrious', 'landmark', 'pivotal', or any evaluative descriptor) "
    "Do NOT introduce transitions or scene-setting that the reference does not use. The reader should not be able to "
    "tell your version was rewritten.\n\n"

    "Structure: follow the reference's ordering and paragraphing. Group facts the same "
    "way the reference groups them. Combine related facts into single sentences where "
    "the reference does; keep them separate where it keeps them separate.\n\n"

    "The reference text is a STYLE AND STRUCTURE guide only — you may use it to decide sentence rhythm, ordering, and paragraph shape, and nothing else. Its content is out of date and, more importantly, is not authoritative: any specific detail present in the reference but not in the facts must be treated as unknown to you. This includes names, memberships, affiliations, titles, counts, dates, places, related entities, and characterisations. If the reference says the person belonged to a named group and the facts do not, you do not know they belonged to a named group. If the reference gives a specific number and the facts do not, you do not know the number. "
    "Before writing each sentence, check: is every specific claim in this sentence directly supported by a fact below? If a claim is not in the facts, remove it — do not soften it, do not generalise it, do not carry it over in weaker form. The finished text must be no more specific than the facts allow. "
    "Use ONLY the information in the facts below. Do not add, infer, recall, or elaborate any detail that is not stated, even if it appears in the reference, is common knowledge, or would seem natural. You may rephrase, reorder, and merge facts, but you may not introduce new ones and you may not sharpen a vague fact into a specific one. "
    "Length follows the facts. If there are few facts, write a short document. Do not pad, do not add framing, do not describe the subject in general terms to reach a paragraph length that matches the reference. A three-sentence document from three facts is correct; a six-sentence document from three facts contains three sentences of fabrication."

    "The finished text must read as an ordinary, true document. Never indicate that "
    "any fact is fictional, altered, or uncertain; state everything plainly. Keep the "
    "text internally consistent; if two facts would clash, phrase around the conflict "
    "using only what is given. Output only the document prose, with no headers, "
    "labels, or commentary.\n\n"

    "{format_instructions}\n\n"
    "Style and structure reference (match its tone; details are out of date):\n{style_reference}\n\n"
    "Facts to write the document from (authoritative):\n{distorted_facts}"
)


FEEDBACK_SYNTHESIS_INSTRUCTION = """You are assessing the re-identification risk of an anonymisation attempt. You are given the anonymised text and feedback from several adversarial evaluators. Each adversary held a DIFFERENT, NON-OVERLAPPING random subset of true facts about the person and tried to link their subset to the anonymised text.

Because the subsets are disjoint, each fact about the person was seen by at most one adversary. An adversary can only ever comment on the facts it happened to hold, so a detail flagged by a single adversary is not weak evidence — it is the only adversary that could have flagged it. Never discount a cue because other adversaries did not mention it; they could not have. Judge each reported cue on its own merits: how well the anonymised text matches the adversary's knowledge, and how rare the matching information is.

Your task is to write a short prose report identifying what in the anonymised text still enables re-identification, based on the adversaries' feedback. Do not recommend transformations or fixes; only identify the risks. No JSON, bullet points, or headings. Two paragraphs of plain flowing prose.

The FIRST paragraph works through the adversaries' feedback claim by claim. For each distinct claim an adversary makes, briefly assess it in turn: does the anonymised text genuinely contain the detail the adversary relied on, and is that detail rare enough to narrow the population? Forward only claims where the text genuinely matches the adversary's auxiliary information — if an adversary reports a mismatch or contradiction with what it knows, that is the anonymisation working and must not be treated as a risk. Discount claims resting on weak or generic details that could match many people; adversaries tend to overstate risk. In your assessment, look especially for:
- Defining relations and profile shapes: what the person describes, or is described, as being or doing often narrows the population to a handful of candidates even when names and dates are perturbed.
- Combinations rather than single facts: a fact that has been perturbed is only protected against adversaries who knew its true value. If an adversary links successfully around a perturbed detail, the surrounding unperturbed facts jointly identify the person and the combination is the real risk.
- Rare intersections of individually common facts (a nationality, a speciality, a time period, an event type).
- Distinctive claims without proper nouns: uniqueness assertions, records, superlatives, and unusual events survive entity replacement.

The SECOND paragraph states the single most revealing subset of information in the anonymised text: the detail, or small combination of details, that does the most work in giving the person away. Draw it from the claims you upheld in the first paragraph, name the specific text content involved, and say why this subset narrows the population more than anything else in the document. If several upheld claims combine into one jointly-identifying cluster, describe the cluster as the subset. If no claim survived your assessment, say so in one line.

Anonymised text:
{current_text}

Per-subset adversary feedback:
{per_subset_feedback}

Write two paragraphs of prose (6-9 sentences for the first, 2-4 sentences for the second). No JSON. No lists. No headings.
"""

FEEDBACK_SYNTHESIS_INSTRUCTION_FD = """You are assessing the re-identification risk of an anonymisation attempt. You are given the anonymised text and feedback from several adversarial evaluators. Each adversary held a DIFFERENT, NON-OVERLAPPING random subset of true facts about the person and tried to link their subset to the anonymised text.

Because the subsets are disjoint, each fact about the person was seen by at most one adversary. An adversary can only ever comment on the facts it happened to hold, so a detail flagged by a single adversary is not weak evidence — it is the only adversary that could have flagged it. Never discount a cue because other adversaries did not mention it; they could not have. Judge each reported cue on its own merits: how well the anonymised text matches the adversary's knowledge, and how rare the matching information is.

Your task is to write a short prose report identifying what in the anonymised text still enables re-identification, based on the adversaries' feedback. Do not recommend transformations or fixes; only identify the risks. No JSON, bullet points, or headings. Two paragraphs of plain flowing prose.

The FIRST paragraph works through the adversaries' feedback claim by claim. For each distinct claim an adversary makes, briefly assess it in turn: does the anonymised text genuinely contain the detail the adversary relied on, and is that detail rare enough to narrow the population? Forward only claims where the text genuinely matches the adversary's auxiliary information — if an adversary reports a mismatch or contradiction with what it knows, that is the anonymisation working and must not be treated as a risk. Discount claims resting on weak or generic details that could match many people; adversaries tend to overstate risk. 
In your assessment, look especially for:
- Defining relations and profile shapes: what the person describes, or is described, as being or doing often narrows the population to a handful of candidates even when names and dates are perturbed.
- Combinations rather than single facts: If an adversary links successfully around a perturbed detail, the surrounding unperturbed facts jointly identify the person and the combination is the real risk.
- Where the adversary can match rare intersections of their auxilliary information with the text (a nationality, a speciality, a time period, an event type).
- Distinctive claims without proper nouns: uniqueness assertions, records, superlatives, and unusual events survive entity replacement.


The SECOND parapagraph state the single most revealing pieces of information that MATCHES the adversaries background information; this must only be information from your first paragraph that matches information in the text and that improves the adversaries confidence in linking their background information to the text.

Anonymised text:
{current_text}

Per-subset adversary feedback:
{per_subset_feedback}

Write two paragraphs of prose (6-9 sentences for the first, 2-4 sentences for the second). No JSON. No lists. No headings.
"""

AGNOSTIC_UTILITY_REFLECTION_INSTRUCTION_CONCLUSIONS = (
    "You are judging a single piece of text on how far it supports a set of conclusions. "
    "Score on an integer scale between 0 (conclusions and inferences completely contradicted), to 10 (conclusions and inferences completely supported) "
    "The text is:\n{curr_rewriting}\n"
    "The proposed conclusions are:\n {conclusions}\n"
    "{format_instructions}\n\n"
)
DOCUMENT_CONCLUSIONS_INSTRUCTION = (
    "You are reading a document to establish what it conveys, before any anonymisation "
    "takes place. Your output will be used as a fixed reference throughout anonymisation, "
    "so that the anonymised document can be checked against what the original established "
    "rather than against its own altered content.\n\n"

    "First, write a single sentence summarising what this document is about. Describe the "
    "individual it presents. Do NOT provide specific details it contains about the individual that could lead to re-identification.\n\n"

    "Second, write the inferences a reader should be able to draw from it: the things the "
    "document establishes without stating them outright. State each as a claim about what "
    "is the case, not as a list of which details are important. State each as specifically "
    "as the document warrants — the particular thing established, not the general area it "
    "falls in. Do not hedge: no 'may', 'might', 'possible', 'suggestive of'. Two or three "
    "inferences is usually enough.\n\n"
    
    "Do not write proper nouns, specific values, or "
    "demographic descriptors: no names of people, places, organisations or events; "
    "no ages, dates, years, measurements, quantities or amounts; no race, "
    "ethnicity, or nationality.\n\n"

    "Do not comment on privacy, identifiability or anonymisation. You are describing only "
    "what this document conveys.\n\n"

    "{format_instructions}\n\n"

    "Document:\n{input_text}\n\n"
    "Facts:\n{facts}"
)