from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

from config.company_info import COMPANY_NAME, SUPPORT_EMAIL, SUPPORT_PHONE

load_dotenv()

# Set GEMINI_API_KEY for LiteLLM
os.environ["GEMINI_API_KEY"] = os.environ.get("GOOGLE_API_KEY", "")

# We use the liteLLM string format for Gemini
llm_model = "gemini/gemini-2.5-flash"

def format_customer_response(user_query: str, agent_context: str, customer_name: str = None) -> str:
    """
    Uses CrewAI to draft a professional response to the customer based on the context.
    """
    
    # Define Agents
    writer = Agent(
        role='Communications Specialist',
        goal='Draft clear, empathetic, and professional responses to customer inquiries using the provided agent context.',
        backstory='You are an expert customer support specialist at Prodapt telecom. You synthesize complex technical or billing data into easy-to-understand messages for the customer. CRITICAL: Financial statuses must NEVER be changed. If context contains PENDING_APPROVAL, APPLIED, REJECTED, or UNDER_REVIEW, your output must preserve that exact status meaning without alteration (e.g., never say a pending credit is approved).',
        verbose=True,
        allow_delegation=False,
        llm=llm_model
    )
    
    reviewer = Agent(
        role='Quality Reviewer',
        goal='Review the drafted response for accuracy, tone, and policy compliance.',
        backstory='You are the senior communications manager at Prodapt. You ensure every email sent to customers is polite, accurate, policy compliant, and reflects well on the brand. You strictly ensure that financial statuses (PENDING_APPROVAL, APPLIED, REJECTED, UNDER_REVIEW) are not misrepresented.',
        verbose=True,
        allow_delegation=False,
        llm=llm_model
    )
    
    greeting_name = customer_name if customer_name else "Valued Customer"
    
    # Define Tasks
    draft_task = Task(
        description=f"""The customer asked: '{user_query}'. Based on the following information retrieved from our systems (agent_context), draft a polite email response: 
{agent_context}

Make sure to answer their question fully based ONLY on the provided context. 

CRITICAL RULES:
1. Start the email EXACTLY with: 'Dear {greeting_name},'
2. Never invent or hallucinate the customer's name. Use exactly the greeting provided above.
3. If the context contains a status like PENDING_APPROVAL, APPLIED, REJECTED, or UNDER_REVIEW, clearly state that exact status. Never rewrite pending as approved.
4. Only append the company contact information ({COMPANY_NAME}, Email: {SUPPORT_EMAIL}, Phone: {SUPPORT_PHONE}) if this is an escalation, requires manual approval, has missing information, remains unresolved, or needs a support ticket. Do NOT append contact info to every response. Never invent contact info.""",
        expected_output="A well-written, polite email drafted for the customer.",
        agent=writer
    )
    
    review_task = Task(
        description="Review the draft email. Ensure the tone is empathetic and policy compliant. Verify that no financial statuses (like PENDING_APPROVAL) were hallucinated or incorrectly modified to seem fully resolved if they are still pending. Output the final text only.",
        expected_output="The final, polished email ready to be sent to the customer.",
        agent=reviewer
    )
    
    # Form the Crew
    crew = Crew(
        agents=[writer, reviewer],
        tasks=[draft_task, review_task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return str(result)

if __name__ == "__main__":
    # Test
    q = "Customer CUST-10002 was charged twice. My name is John Smith."
    c = "Successfully applied $50.0 credit to CUST-10002 for 'Duplicate charge refund'. New balance is $0.0. Status: PENDING_APPROVAL"
    print(format_customer_response(q, c, "John Smith"))
