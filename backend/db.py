from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, Session
import logging
from typing import List
from definitions import PGDocument, FypDocs

Base = declarative_base()


class Database:
    """Simple database wrapper for the app."""

    def __init__(self, conn_string: str):
        self.engine = create_engine(conn_string, echo=True)
        self._connect()

    def _connect(self):
        try:
            self.connection = self.engine.connect()
        except OperationalError as err:
            logging.error(f"Error connecting to database: {err}")
            raise err

    def _setup(self):
        """Create the fyp_docs table if it doesn't exist."""
        insp = inspect(self.engine)
        if not insp.has_table('fyp_docs'):
            logging.info("Creating fyp_docs table...")
            FypDocs.metadata.create_all(self.engine)
            logging.info("Created fyp_docs table.")
        else:
            logging.info("fyp_docs table already exists.")

    def insert_document(self, document: PGDocument):
        """Insert a new document into the database.

        :param document: The document to be inserted. :class `Document`

        :return: None
        """
        with Session(self.engine) as session:
            new_doc = FypDocs(id=document.id,
                              path=document.path,
                              name=document.name,
                              pages_with_charts_idx=document.pages_with_charts_idx,
                              parsed_data=document.parsed_data,
                              bboxes=document.bboxes,
                              width=document.width,
                              height=document.height)
            session.add(new_doc)
            print(f"Inserting document...{new_doc}")
            session.commit()

    def get_document(self, doc_id: str) -> FypDocs:
        """Get a document from the database.

        :param doc_id: The ID of the document. :class `str`

        :return: The document instance if found, else None.
        """
        with Session(self.engine) as session:
            return session.query(FypDocs).filter_by(id=doc_id).first()
        
    def get_documents(self, doc_ids: List[str]) -> List[FypDocs]:
        """Get a list of documents from the database.

        :param doc_ids: A list of document IDs. :class `List[str]`

        :return: A list of document instances.
        """
        with Session(self.engine) as session:
            return session.query(FypDocs).filter(FypDocs.id.in_(doc_ids)).all()

    def get_all_documents(self) -> List[FypDocs]:
        """Get all documents from the database.

        :return: A list of all documents in the database.
        """
        with Session(self.engine) as session:
            return session.query(FypDocs).all()
