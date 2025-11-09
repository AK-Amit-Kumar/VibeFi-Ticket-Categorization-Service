import json
from enum import Enum  #created for setting constant values for further us
from typing import List, Literal  #making sure string values getting specific set of values
from fastapi import FastAPI, HTTPException  #Importing FASTApi components, raising exception if any issue encountered
from pydantic import BaseModel, Field #for  defining structure for I/O model and description to the fields

#Setting Input and Output Data Models

#Defining possible action types
class ActionType(str, Enum):
    #The final decision for resolving the Banking tickets
    AI_CODE_PATCH = "AI_CODE_PATCH"          #bugs, system failures, logic errors
    VIBE_WORKFLOW = "VIBE_WORKFLOW"          #Known procedural issues, user errors

#Input Data Model
class TicketInput(BaseModel):
    channel: str = Field(..., description="Source of the ticket")
    severity: Literal["critical", "high", "medium", "low"] = Field(..., description="The urgency(priority) of the ticket.")
    summary: str = Field(..., description="Breif description of the problem")

#Output Data Model
class ActionPlan(BaseModel):
    decision: ActionType = Field(..., description="The chosen type of Action")
    reasoning: str = Field(..., description="Explanation for the decided type of Action")
    next_actions_checklist: List[str] = Field(..., description="Lightweight checklist for next actions")

# --- CORE LOGIC: CATEGORIZATION lOGIC ---
# Logic to categorize the ticket based on severity and keywords in the summary.

    #Input - 'TicketInput' Data model
    #Output - 'ActionPlan' Data model
    # Creating RULE BASED SYSTEM for determining the best action for that specific ticket

def categorize_ticket(ticket: TicketInput) -> ActionPlan:

    summary_lower = ticket.summary.lower()
    severity = ticket.severity.lower()
    
    
    # Rule 1: Critical or High Severity with System Failure Keywords
    if severity in ["critical", "high"]:
        code_keywords = ["error", "failure", "bug", "404", "500", "incorrect calculation", "database", "api down", "system crash"]
        if any(keyword in summary_lower for keyword in code_keywords):
            return ActionPlan(
                decision=ActionType.AI_CODE_PATCH,
                reasoning=f"Severity is **{severity.upper()}** and summary suggests a core system/code failure (`{ticket.summary}`).",
                next_actions_checklist=[
                    "Verify bug is reproducible in staging environment.",
                    "Create a detailed Jira ticket linking logs.",
                    "Tag SRE team for immediate monitoring."
                ]
            )
    
    # Rule 2: High Severity in sensitive banking operations
    if severity == "high" and any(keyword in summary_lower for keyword in ["fraud", "transaction", "payment processing"]):
        return ActionPlan(
            decision=ActionType.AI_CODE_PATCH,
            reasoning=f"Severity is **HIGH** and involves a critical financial process (`{ticket.summary}`). Likely requires code audit/patch.",
            next_actions_checklist=[
                "Immediately freeze affected user accounts/processes.",
                "Alert compliance and security teams.",
                "Capture full transaction log details."
            ]
        )

    
    # Rule 3: Low/Medium Severity with Account,Credential keywords
    if severity in ["medium", "low"]:
        workflow_keywords = ["forgot password", "reset pin", "locked", "account blocked", "rate limit", "cannot log in", "update address"]
        if any(keyword in summary_lower for keyword in workflow_keywords):
            return ActionPlan(
                decision=ActionType.VIBE_WORKFLOW,
                reasoning=f"Severity is **{severity.upper()}** and issue relates to known user/account procedural action. Vibe workflow exists.",
                next_actions_checklist=[
                    "Run Vibe Script 'User-Account-Unblock-v1.0'.",
                    "Confirm two-factor authentication reset with user via secure channel.",
                    "Document successful run in the ticket notes."
                ]
            )

    # Rule 4: General Inquiry or Request (low-impact)
    if any(keyword in summary_lower for keyword in ["how to", "question about", "need help with", "inquire"]):
        return ActionPlan(
            decision=ActionType.VIBE_WORKFLOW,
            reasoning="The ticket appears to be a general inquiry or procedural request, best handled by a documented Vibe troubleshooting script.",
            next_actions_checklist=[
                "Check internal knowledge base for an existing Vibe script.",
                "Reply with documented steps/FAQ link.",
                "If no Vibe script exists, manually triage to L1 support."
            ]
        )

    # --- DEFAULT TICKETS TO BE HANDLED ---
    # Any high/critical ticket that was missed earlier is assumed to be a system issue.
    if severity in ["critical", "high"]:
        return ActionPlan(
            decision=ActionType.AI_CODE_PATCH,
            reasoning=f"Default routing for **{severity.upper()}** tickets. System failure is the most cautious default.",
            next_actions_checklist=[
                "Manually triage to L2 developer support.",
                "Review the system health dashboard immediately.",
                "Capture full user session data."
            ]
        )
    
    # Default code for handling regular Procedural check
    return ActionPlan(
        decision=ActionType.VIBE_WORKFLOW,
        reasoning="Default routing for unclassified medium/low severity tickets, assumed to be procedural.",
        next_actions_checklist=[
            "Escalate to the appropriate L1 support queue for manual review.",
            "Monitor ticket for 30 minutes for any change in status."
        ]
    )


# *** API SETUP ***

app = FastAPI(
    title="VibeFI AI Ticket Categorization Service",
    description="A service to categorize banking support tickets and generate an appropriate action plan.",
    version="1.0.0"
)

@app.post("/categorize", response_model=ActionPlan, status_code=200)
async def classify_ticket_endpoint(ticket: TicketInput):
    
    # Accepts a banking support ticket and returns the appropriate action plan: 
    try:
        # Passing the validated Pydantic model directly to the core logic
        result = categorize_ticket(ticket)
        return result
    except Exception as e:
        # Error handling
        raise HTTPException(status_code=500, detail=f"Internal classification error: {str(e)}")
