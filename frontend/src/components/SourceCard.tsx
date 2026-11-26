import {ExternalLink,FileText,Quote} from "lucide-react";
import type {EvidenceItem,SupportingQuote} from "../types";
export default function SourceCard({item,index}:{item:EvidenceItem|SupportingQuote;index:number}){
 const e=item as EvidenceItem;const q=(item as SupportingQuote).quote||e.quote||e.exact_text||"";
 const title=e.document_title||e.title||e.document_id||e.evidence_id||`Source ${index+1}`;
 const page=e.page_number??e.pdf_page_number;const url=e.official_url||e.source_url;
 return <article className="source-card"><div className="source-icon"><FileText size={16}/></div><div className="source-content"><div className="source-topline"><span className="source-label">OFFICIAL EVIDENCE · {String(index+1).padStart(2,"0")}</span>{page!==undefined&&<span className="page-pill">Page {page}</span>}</div><h4>{title}</h4>{q&&<p className="source-quote"><Quote size={12}/>{q}</p>}{url&&<a className="source-link" href={url} target="_blank" rel="noreferrer">Open source <ExternalLink size={12}/></a>}</div></article>
}