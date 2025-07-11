from ai.agent_utils import run_multi_llm
from ai.prompts import self_audit_prompt
from core.proposals import fetch_pending_proposals
from core.cypher_actuator import is_safe_cypher, run_cypher_actuator
from proposal_executor import review_with_llm

def process_cypher_proposal(cypher, verdict, review_reason):
    if verdict == "approve":
        print("LLM approved. Attempting Cypher execution…")
        try:
            if is_safe_cypher(cypher):
                success, exec_result = run_cypher_actuator(cypher)
                if success:
                    print(f"Cypher executed: {exec_result}")
                else:
                    print(f"Execution error: {exec_result}")
            else:
                print("Blocked dangerous Cypher! Not executed.")
        except Exception as e:
            print(f"Exception during Cypher execution: {e}")
    else:
        print(f"Proposal rejected by LLM: {review_reason}")

def review_pending_proposals():
    proposals = fetch_pending_proposals()
    for prop in proposals:
        print(f"Pending Proposal: Cypher={prop['cypher']}\nReason={prop['reason']}\nSource={prop['source']}\nMeta={prop['meta']}\n---")
        review = review_with_llm(prop['cypher'], prop['reason'])
        verdict = review.get("verdict", "reject")
        review_reason = review.get("reason", "No reason provided.")
        process_cypher_proposal(prop['cypher'], verdict, review_reason)

def main():
    # First, review and possibly execute proposals
    review_pending_proposals()

    # Then run the audit
    prompt = self_audit_prompt()
    results = run_multi_llm(prompt, agent_type="audit")
    for r in results:
        print(f"Agent {r['agent']} audit:\n{r['output']}\n")

if __name__ == "__main__":
    main()
