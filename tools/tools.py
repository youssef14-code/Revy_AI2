from langchain_core.tools import tool
from tools.services import BookingService, MemoryService
from retrival.retriever import RetrievalService

def create_booking_tool(user):  # ← رجّع user هنا
    
    @tool
    def book_appointment(
        name: str,
        day: str,        # ← بدل appointment_date
        time: str,       # ← ضيف time
        phone_number: str,
        description: str = ""  # ← بدل service_name
    ) -> dict:
        """
        Book a business appointment or meeting for a client.
        Only call this tool when you have all required fields AND client confirms.
        Fields needed: day, time, phone_number, and optionally description (e.g. 'AI Agent consultation', 'Business meeting').
        """
        result = BookingService.book(
            name=name,          # ← ضيف user
            day=day,
            time=time,
            phone_number=phone_number,
            description=description
        )

        if result:
            return {
                "status": "success",
                "message": f"✅ تم الحجز ليوم {day} الساعة {time}",
            }
        else:
            return {
                "status": "error",
                "message": "❌ فشل الحجز في قاعدة البيانات"
            }

    return book_appointment

  


# -----------------------------
# RAG Tool
# -----------------------------
def create_rag_tool():
    
    @tool
    def query_knowledge_base(question: str) -> str:
        """
        Search the company knowledge base to answer questions about:
        - RevyAI services, solutions, and capabilities
        - AI agents and automation systems
        - Company policies, rules, and operational guidelines
        - Pricing, integration, deployment, or technical details
        
        Use this tool whenever the user asks anything about the company or its offerings.
        Do NOT use this tool for greetings, booking appointments, or unrelated questions.
        """
        return RetrievalService().search(question)

    return query_knowledge_base