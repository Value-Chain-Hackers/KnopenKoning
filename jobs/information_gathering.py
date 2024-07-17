from wikipedia import search, page, summary
from duckduckgo_search import DDGS
from db import Company, Records, Website
from sqlalchemy.orm import Session




def collect_base_information(company_name: str, db: Session):
    company = db.query(Company).filter(Company.company_name == company_name).first()
    records = db.query(Records).filter(Records.company_id == company.id).all()
    # If we have records, return them
    if records:
        return records
    
    # If we don't have records, we need to collect them
    search_results = search(company.company_name)
    if not search_results:
        return None
    pages = []
    for result in search_results:
        try:
            page_summary = summary(result)
            page_result = page(result)
            
            with open(f"./.cache/{company.company_name}/{result}.md", "w") as f:
                f.write(f"# {page_result.title}\n\n")
                f.write(f"## Summary\n\n")
                f.write(page_summary)
                f.write("\n\n")
                for section in page_result.sections:
                    f.write(f"\n\n### {section.title}\n\n")
                    f.write(section.content)
                f.write("\n\n")
                
                f.write(f"## Links\n\n")
                for link in page_result.links:
                    f.write(f"\n\n[{link}]({link})")
                f.write("\n\n")
                
                f.write(f"## References\n\n")
                for reference in page_result.references:
                    f.write(f"\n\n[{reference}]({reference})")
                f.write("\n\n")
                
                f.write(f"## Images\n\n")
                for image in page_result.images:
                    f.write(f"\n\n![Image]({image})")
                    


            # Save the page content to a file and save the path to the database
            record = Records(company_id=company.id, record_type="wikipedia", record_name=result, record_path=result + ".txt")
            db.add(record)
            db.commit()
            records.append(record)

        except Exception as e:
            continue
    return records

class InformationQueryBuilder():
    
    def __init__(self, db: Session):
        self.db = db
        self.duckduckgo = DDGS()

    def get_company_records(self, company_name: str):
        company = self.db.query(Company).filter(Company.company_name == company_name).first()
        records = self.db.query(Records).filter(Records.company_id == company.id).all()
        return records
    
    def get_company_websites(self, company_name: str):
        company = self.db.query(Company).filter(Company.company_name == company_name).first()
        websites = self.db.query(Website).filter(Website.company_id == company.id).all()
        return websites
    
    def get_company_information(self, company_name: str):
        self.duckduckgo.s


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--company", type=str, required=True)
    args = parser.parse_args()


    from db.session import SessionLocal
    db = SessionLocal()
    collect_base_information(args.company, db)
    db.close()