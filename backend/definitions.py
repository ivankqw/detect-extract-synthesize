from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, validates

Base = declarative_base()


class FypDocs(Base):
    __tablename__ = 'fyp_docs'

    id = Column(String, primary_key=True, index=True)
    path = Column(String, nullable=False)
    name = Column(String, nullable=False)
    pages_with_charts_idx = Column(ARRAY(Integer))
    parsed_data = Column(String)
    bboxes = Column(ARRAY(Float, dimensions=3))
    width = Column(Integer)
    height = Column(Integer)

    @validates('bboxes')
    def validate_bboxes(self, key, bboxes):
        if bboxes is not None:
            # Check if the bboxes is a three-dimensional array
            if not (isinstance(bboxes, list) and
                    all(isinstance(sublist, list) for sublist in bboxes) and
                    all(isinstance(subsublist, list) for sublist in bboxes for subsublist in sublist)):
                raise ValueError("bboxes must be a three-dimensional list")
            # Optionally, you can add more checks for the inner dimensions
        return bboxes


@dataclass
class PGDocument:
    path: str
    name: str
    id: str
    parsed_data: str
    pages_with_charts_idx: list
    bboxes: list
    width: int
    height: int

    def to_dict(self):
        return {
            "path": self.path,
            "name": self.name,
            "id": self.id,  # "uid" is the id for the document
            "parsed_data": self.parsed_data,
            "bboxes": self.bboxes,
            "width": self.width,
            "height": self.height
        }

    @staticmethod
    def from_dict(self, data: dict):
        self.path = data["path"]
        self.name = data["name"]
        self.id = data["id"]
        self.parsed_data = data["parsed_data"]
        self.bboxes = data["bboxes"]
        self.width = data["width"]
        self.height = data["height"]


def extraction_prompt(doc_name: str):
    return f"""
This is a page from a pitchdeck for the document named {doc_name}. It may include details on the startup's name, product, business model, market size, competition, founders, traction, unit economics, P&L shape, investment scope, exit potential, and current investors list.

Please extract all relevant information from this page. Additionally, you will encounter one or more graphs annotated with bounding boxes. Based on these graphs, provide a detailed overview of the startup's documentation, covering a wide range of aspects essential for a comprehensive understanding of its potential and current status:

- **Sector/Business Model**: Examine the startup's industry and business model. Consider its position within the broader ecosystem and any innovative strategies it employs.
- **Product & Value Proposition**: Detail the startup's products or services and the unique advantages they offer to customers. Discuss how these offerings differentiate in the market.
- **Competition/Moat**: Analyze the startup's competitive landscape, including proprietary technology, strategic partnerships, or established barriers to entry.
- **Founder Background**: Offer insights into the founders' expertise, past ventures, and their vision for the company. Emphasize any unique experiences or qualifications that support the startup's success.
- **Market Size**: Evaluate the market opportunity for the startup's offerings. Look at current market conditions and future growth potential.
- **Impact**: Assess the tangible and intangible impacts of the startup's products or services on its customers and the industry.
- **Current Traction**: Summarize key performance indicators, such as user growth, financial metrics (revenue, profit, expenses), and market penetration for the current and previous years, assuming the current year is 2024.
- **Unit Economics**: Discuss the startup's cost structure and revenue model. Provide insights into customer acquisition costs, retention costs, and the lifetime value of a customer.
- **P&L Shape**: Describe the startup's financial health and profitability trends, including major cost drivers and revenue streams.
- **Investment Scope**: Outline the startup's funding goals, including the capital being raised, intended use of funds, and any pre-money or post-money valuations.
- **Exit Potential**: Analyze potential exit strategies for the startup, considering industry trends, historical acquisitions, and the current investment climate. Discuss potential acquirers and whether an IPO or acquisition is more likely.
- **List of Current Investors**: Compile a list of current investors, their investment stages, and any strategic alignments or partnerships that may affect the startup's path.

Link the graphs to the rest of the page to construct your analysis comprehensively. If certain information is not explicitly presented or is ambiguous, omit it.

Guiding FAQs for your analysis:
- "What is the startup's competitive advantage/moat?"
- "What can we infer about the market size for the startup's product or service?"
- "What is the potential market opportunity for the startup's product or service?"
- "What is the startup's revenue this year and last year, taking this year as 2024?"
- "What are the startup's expenses this year and last year, taking this year as 2024?"
- "What is the customer acquisition cost (CAC)?"
- "What is the retention cost?"
- "What is the customer lifetime value (CLTV)?"
- "What are the profitability trends for the startup?"
"""
