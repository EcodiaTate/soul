import json
import logging
from core.db import get_session
from core.proposals import fetch_pending_proposals
from ai.agent_utils import run_multi_llm

logging.basicConfig(level=logging.INFO, filename="logs/proposal_executor.log")

LLM_REVIEW_PROMPT = (
    "You are an expert Neo4j administrator and AI safety auditor. "
    "Analyze the following Cypher query proposal for safety, intent, and best practice. "
    "Respond with a JSON containing: "
    '{"verdict": "approve/reject", "reason": "...", "suggested_correction": "<if_any>"}\n\n'
    "Proposal:\n{cypher}\n\nReason for proposal: {reason}\n"
)

def review_with_llm(cypher, reason):
    prompt = LLM_REVIEW_PROMPT.format(cypher=cypher, reason=reason)
    results = run_multi_llm(prompt, agent_type="cypher_audit")
    # Expecting: [{"output": {"verdict": "approve", "reason": "...", ...}, ...}]
    for r in results:
        try:
            out = r["output"]
            if isinstance(out, str):
                out = json.loads(out)
            if "verdict" in out:
                return out
        except Exception as e:
            logging.error(f"LLM review parse error: {e}")
    return {"verdict": "reject", "reason": "LLM review failed to parse response."}

def execute_cypher(cypher):
    with get_session() as session:
        try:
            result = session.run(cypher)
            return True, [r.data() for r in result]
        except Exception as e:
            logging.error(f"Cypher execution error: {e}")
            return False, str(e)

def update_proposal_status(proposal_id, status, review_reason, execution_result=None):
    with get_session() as session:
        session.run("""
            MATCH (p:Proposal) WHERE id(p) = $proposal_id
            SET p.status = $status, p.review_reason = $review_reason, p.execution_result = $execution_result
        """, proposal_id=proposal_id,
           status=status,
           review_reason=review_reason,
           execution_result=json.dumps(execution_result) if execution_result else ""
        )

def main():
    proposals = fetch_pending_proposals()
    if not proposals:
        print("No pending proposals.")
        return

    for prop in proposals:
        pid = prop['id']
        cypher = prop['cypher']
        reason = prop['reason']

        print(f"\n=== Reviewing Proposal {pid} ===")
        print(f"Cypher: {cypher}\nReason: {reason}")

        review = review_with_llm(cypher, reason)
        verdict = review.get("verdict", "reject")
        review_reason = review.get("reason", "No reason provided.")

        if verdict == "approve":
            print(f"Proposal {pid} APPROVED by LLM. Executing Cypher...")
            success, exec_result = execute_cypher(cypher)
            if success:
                print(f"Proposal {pid} executed successfully.")
                update_proposal_status(pid, "executed", review_reason, exec_result)
            else:
                print(f"Execution failed: {exec_result}")
                update_proposal_status(pid, "execution_failed", review_reason, exec_result)
        else:
            print(f"Proposal {pid} REJECTED by LLM: {review_reason}")
            update_proposal_status(pid, "rejected", review_reason)

if __name__ == "__main__":
    main()
