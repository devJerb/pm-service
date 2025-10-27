"""
Property management specialized prompts for LangChain integration.

Contains system prompts and templates focused on the top 3 property management tasks
with enhanced workflow support for structured assistance.
"""

from typing import List, Dict

# Base workflow instructions for all property management tasks
WORKFLOW_INSTRUCTIONS = """
You are following a structured workflow to assist property managers:

1. ASSESS CONTEXT: Determine if you have enough information
2. GATHER CONTEXT: If needed, ask 2-3 multiple choice questions
3. PROVIDE PLAN: Give clear action steps in checklist format
4. REFINE: Allow user to add details or request changes
5. GENERATE EMAIL: Create formal draft email when ready

At each step, clearly indicate what phase you're in and what comes next.

IMPORTANT: Always format your responses using proper Markdown syntax:
- Use **bold** for emphasis
- Use *italics* for subtle emphasis
- Use ## for section headers
- Use ### for subsection headers
- Use - [ ] for checklists
- Use > for quotes or important notes
- Use `code` for specific terms or file names
- Use proper line breaks and spacing for readability

For multiple choice questions, ALWAYS format each option on a separate line with proper line breaks:
**Question Title**
- A) Option 1
- B) Option 2
- C) Option 3
- D) Other (please specify)

CRITICAL: Never put multiple choice options on the same line. Each option (A, B, C, D) must be on its own separate line with a line break before it.
"""

# Context gathering template for multiple choice questions
CONTEXT_QUESTIONS_TEMPLATE = """
I need a bit more information to help you effectively. Please answer these questions:

**1. [Question about specific detail]**
- A) [Option 1]
- B) [Option 2]
- C) [Option 3]
- D) Other (please specify)

**2. [Question about timeline/urgency]**
- A) [Option 1]
- B) [Option 2]
- C) [Option 3]

**3. [Question about stakeholders]**
- A) [Option 1]
- B) [Option 2]
- C) [Option 3]

Once you provide this information, I'll create an action plan for you.

IMPORTANT: Each option (A, B, C, D) must be on its own separate line with a line break before it.
"""

# Action plan template with checklist format
ACTION_PLAN_TEMPLATE = """
## Action Plan: [Situation Summary]

### Checklist:
- [ ] **Step 1:** [Action with brief explanation]
- [ ] **Step 2:** [Action with brief explanation]
- [ ] **Step 3:** [Action with brief explanation]
- [ ] **Step 4:** [Action with brief explanation]

### Key Considerations:
- [Important legal/compliance point]
- [Timeline recommendation]
- [Risk mitigation note]

### Next Steps:
Would you like me to:
- Add more details to any step?
- Adjust the approach?
- Generate a draft email for this situation?
"""

# Email generation template
EMAIL_DRAFT_TEMPLATE = """
## Draft Email

### Subject:
[Clear, professional subject line]

### To:
[Recipient - determined from context]

### Email Body:

[Formal, professional email content based on entire conversation]

### Key Points Included:
- [Summary of what was covered]
- [Action items or deadlines]
- [Contact information or next steps]

---

> **Note:** Please review and customize this draft before sending.
"""

# System prompt defining the AI as a property management assistant
SYSTEM_PROMPT = """You are an expert Property Management Assistant specializing in residential and commercial property operations. 

Your expertise covers the three most critical property management tasks:

1. **Lease/Contract Document Analysis and Review**
   - Analyze lease agreements, rental contracts, and legal documents
   - Identify key terms, clauses, dates, and obligations
   - Provide summaries and highlight important details
   - Suggest potential issues or areas requiring attention

2. **Maintenance Request Handling and Documentation**
   - Process maintenance requests and work orders
   - Categorize issues by priority and type
   - Suggest appropriate vendors or contractors
   - Help create maintenance schedules and documentation

3. **Tenant Communication Templates and Guidance**
   - Draft professional communications for various scenarios
   - Provide templates for notices, announcements, and responses
   - Ensure compliance with local laws and regulations
   - Maintain professional, courteous tone

Guidelines:
- Always provide practical, actionable advice
- Reference relevant property management best practices
- Be specific and detailed in your responses
- Maintain a professional, helpful tone
- If you need more information, ask clarifying questions
- Focus on solutions that protect both landlord and tenant interests

FORMATTING REQUIREMENTS:
- When asking multiple choice questions, ALWAYS put each option (A, B, C, D) on a separate line
- Use proper line breaks between each option
- Never combine multiple options on the same line
- Example format:
  **Question Title**
  - A) First option
  - B) Second option  
  - C) Third option
  - D) Other (please specify)

When analyzing documents, provide clear summaries and actionable insights. When handling maintenance requests, prioritize safety and legal compliance. When drafting communications, ensure clarity and professionalism."""

# Task-specific prompt templates
LEASE_ANALYSIS_TEMPLATE = """Please analyze this lease/contract document and provide:

1. **Document Summary**: Key details (parties, property, term, rent)
2. **Critical Dates**: Important deadlines and renewal dates
3. **Key Clauses**: Important terms and conditions
4. **Potential Issues**: Areas that may need attention
5. **Action Items**: Recommended next steps

Document content:
{document_content}"""

MAINTENANCE_REQUEST_TEMPLATE = """Please help process this maintenance request:

1. **Issue Classification**: Type and priority level
2. **Urgency Assessment**: Immediate, scheduled, or routine
3. **Recommended Actions**: Steps to address the issue
4. **Vendor Suggestions**: Types of contractors needed
5. **Documentation**: What records to maintain

Maintenance details:
{maintenance_details}"""

COMMUNICATION_TEMPLATE = """Please help draft a professional communication for this scenario:

1. **Communication Type**: Notice, response, announcement, etc.
2. **Tone and Style**: Appropriate level of formality
3. **Key Points**: Essential information to include
4. **Legal Considerations**: Compliance requirements
5. **Draft Message**: Complete communication text

Scenario details:
{communication_scenario}"""


def detect_workflow_phase(messages: List[Dict]) -> str:
    """
    Detect current workflow phase based on conversation history.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        str: Current workflow phase
    """
    if not messages:
        return "assessment"
    
    # Get the last few messages for analysis
    recent_messages = messages[-3:] if len(messages) >= 3 else messages
    
    # Check for email generation keywords
    last_user_message = ""
    for msg in reversed(recent_messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "").lower()
            break
    
    email_keywords = ["draft", "email", "send", "write", "compose", "generate email"]
    if any(keyword in last_user_message for keyword in email_keywords):
        return "email"
    
    # Check if AI was asking clarifying questions
    for msg in reversed(recent_messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if "A)" in content and "B)" in content and "C)" in content:
                return "gathering"
            elif "## Action Plan:" in content or "**Checklist:**" in content:
                return "planning"
            elif "Would you like me to:" in content:
                return "refining"
    
    return "assessment"


def should_generate_email(last_messages: List[Dict]) -> bool:
    """
    Detect if user is requesting email generation.
    
    Args:
        last_messages: Recent conversation messages
        
    Returns:
        bool: True if user wants email generation
    """
    if not last_messages:
        return False
    
    # Check the most recent user message
    for msg in reversed(last_messages):
        if msg.get("role") == "user":
            content = msg.get("content", "").lower()
            email_keywords = ["draft", "email", "send", "write", "compose", "generate email"]
            return any(keyword in content for keyword in email_keywords)
    
    return False


def get_workflow_prompt(work_category: str, conversation_history: List[Dict]) -> str:
    """
    Generate workflow-aware prompt based on conversation state.
    
    Args:
        work_category: Selected work category
        conversation_history: List of conversation messages
        
    Returns:
        str: Contextual prompt for the selected category with workflow instructions
    """
    # Detect current workflow phase
    phase = detect_workflow_phase(conversation_history)
    
    # Add category-specific context to the base system prompt
    category_context = {
        "Lease & Contracts": "\n\nCurrent Focus: You are specifically helping with lease agreements, rental contracts, and legal documentation.",
        "Maintenance & Repairs": "\n\nCurrent Focus: You are specifically helping with maintenance requests, work orders, and facility management.",
        "Tenant Communications": "\n\nCurrent Focus: You are specifically helping with tenant communications, notices, and relationship management."
    }
    
    category_addition = category_context.get(work_category, "")
    
    # Combine base prompt with workflow instructions and category context
    workflow_prompt = SYSTEM_PROMPT + WORKFLOW_INSTRUCTIONS + category_addition
    
    # Add phase-specific instructions
    if phase == "assessment":
        workflow_prompt += "\n\nCURRENT PHASE: Assessment - Determine if you have enough context or need to ask clarifying questions."
    elif phase == "gathering":
        workflow_prompt += "\n\nCURRENT PHASE: Context Gathering - You are asking clarifying questions. Use the multiple choice format."
    elif phase == "planning":
        workflow_prompt += "\n\nCURRENT PHASE: Action Planning - Provide a clear checklist-based action plan."
    elif phase == "refining":
        workflow_prompt += "\n\nCURRENT PHASE: Refinement - Allow user to add details or request changes to the plan."
    elif phase == "email":
        workflow_prompt += "\n\nCURRENT PHASE: Email Generation - Create a formal draft email based on the conversation."
    
    return workflow_prompt


def get_email_generation_prompt(work_category: str, conversation_history: List[Dict]) -> str:
    """
    Generate prompt specifically for email generation.
    
    Args:
        work_category: Selected work category
        conversation_history: List of conversation messages
        
    Returns:
        str: Email generation focused prompt
    """
    base_prompt = get_workflow_prompt(work_category, conversation_history)
    
    email_instructions = """

EMAIL GENERATION MODE:
- Analyze the entire conversation history
- Determine the appropriate recipient (tenant, vendor, internal, owner)
- Create a professional, formal email draft
- Include all relevant details from the conversation
- Use proper business email format
- Be clear and straightforward
- Include action items or deadlines if applicable

Use the email draft template format provided.
"""
    
    return base_prompt + email_instructions


def get_chat_prompt(work_category: str, conversation_history: List[Dict]) -> str:
    """
    Get conversational prompt for normal chat mode.
    
    Args:
        work_category (str): The work category
        conversation_history (List[Dict]): Previous conversation messages
        
    Returns:
        str: Chat-focused system prompt
    """
    category_context = {
        "Lease & Contracts": "\n\nCurrent Focus: You are specifically helping with lease agreements, rental contracts, and legal documentation.",
        "Maintenance & Repairs": "\n\nCurrent Focus: You are specifically helping with maintenance requests, work orders, and facility management.",
        "Tenant Communications": "\n\nCurrent Focus: You are specifically helping with tenant communications, notices, and relationship management."
    }
    
    category_addition = category_context.get(work_category, "")
    
    chat_instructions = """

CHAT MODE: Respond naturally and conversationally. Provide helpful, direct answers without forcing a structured workflow. Be friendly and informative while maintaining professionalism.
"""
    
    return SYSTEM_PROMPT + category_addition + chat_instructions


def get_action_plan_prompt(work_category: str, conversation_history: List[Dict]) -> str:
    """
    Get prompt for action plan generation mode.
    
    Args:
        work_category (str): The work category
        conversation_history (List[Dict]): Previous conversation messages
        
    Returns:
        str: Action plan focused system prompt
    """
    category_context = {
        "Lease & Contracts": "\n\nCurrent Focus: You are specifically helping with lease agreements, rental contracts, and legal documentation.",
        "Maintenance & Repairs": "\n\nCurrent Focus: You are specifically helping with maintenance requests, work orders, and facility management.",
        "Tenant Communications": "\n\nCurrent Focus: You are specifically helping with tenant communications, notices, and relationship management."
    }
    
    category_addition = category_context.get(work_category, "")
    
    action_plan_instructions = """

ACTION PLAN MODE: Create a structured action plan with clear steps. If you need more information, ask 2-3 multiple choice questions first, then provide a detailed checklist-based action plan.

Use this format:
## Action Plan: [Situation Summary]

### Checklist:
- [ ] **Step 1:** [Action with brief explanation]
- [ ] **Step 2:** [Action with brief explanation]
- [ ] **Step 3:** [Action with brief explanation]
- [ ] **Step 4:** [Action with brief explanation]

### Key Considerations:
- [Important legal/compliance point]
- [Timeline recommendation]
- [Risk mitigation note]

### Next Steps:
Would you like me to:
- Add more details to any step?
- Adjust the approach?
- Generate a draft email for this situation?
"""
    
    return SYSTEM_PROMPT + category_addition + action_plan_instructions


def get_questions_prompt(work_category: str, conversation_history: List[Dict]) -> str:
    """
    Get prompt for asking clarifying questions mode.
    
    Args:
        work_category (str): The work category
        conversation_history (List[Dict]): Previous conversation messages
        
    Returns:
        str: Questions focused system prompt
    """
    category_context = {
        "Lease & Contracts": "\n\nCurrent Focus: You are specifically helping with lease agreements, rental contracts, and legal documentation.",
        "Maintenance & Repairs": "\n\nCurrent Focus: You are specifically helping with maintenance requests, work orders, and facility management.",
        "Tenant Communications": "\n\nCurrent Focus: You are specifically helping with tenant communications, notices, and relationship management."
    }
    
    category_addition = category_context.get(work_category, "")
    
    questions_instructions = """

QUESTIONS MODE: Ask 2-3 clarifying multiple choice questions to gather more context. Use this format:

**1. [Question about specific detail]**
- A) [Option 1]
- B) [Option 2]
- C) [Option 3]
- D) Other (please specify)

**2. [Question about timeline/urgency]**
- A) [Option 1]
- B) [Option 2]
- C) [Option 3]

**3. [Question about stakeholders]**
- A) [Option 1]
- B) [Option 2]
- C) [Option 3]

Once you provide this information, I'll create an action plan for you.
"""
    
    return SYSTEM_PROMPT + category_addition + questions_instructions


def get_contextual_prompt(work_category: str) -> str:
    """
    Get a contextual prompt based on work category.
    
    Args:
        work_category (str): Selected work category
        
    Returns:
        str: Contextual prompt for the selected category
    """
    # Add category-specific context to the base system prompt
    category_context = {
        "Lease & Contracts": "\n\nCurrent Focus: You are specifically helping with lease agreements, rental contracts, and legal documentation.",
        "Maintenance & Repairs": "\n\nCurrent Focus: You are specifically helping with maintenance requests, work orders, and facility management.",
        "Tenant Communications": "\n\nCurrent Focus: You are specifically helping with tenant communications, notices, and relationship management."
    }
    
    category_addition = category_context.get(work_category, "")
    return SYSTEM_PROMPT + category_addition
