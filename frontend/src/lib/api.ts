import axios from "axios";
import type { ChatResponse } from "../types";
const api=axios.create({baseURL:import.meta.env.VITE_API_BASE_URL||"http://127.0.0.1:8080",timeout:60000,headers:{"Content-Type":"application/json"}});
export async function sendQuestion(question:string):Promise<ChatResponse>{
 const endpoint=import.meta.env.VITE_CHAT_ENDPOINT||"/api/chat";
 const {data}=await api.post<ChatResponse>(endpoint,{question});
 return data;
}
export async function checkBackend():Promise<boolean>{
 try{await api.get(import.meta.env.VITE_HEALTH_ENDPOINT||"/api/health",{timeout:5000});return true;}catch{return false;}
}
export function getApiError(error:unknown):string{
 if(axios.isAxiosError(error)){
  if(error.code==="ECONNABORTED")return "The request took too long. Please try again.";
  if(error.response?.status===404)return "Chat endpoint not found. Check VITE_CHAT_ENDPOINT against your Java PublicController.";
  if(error.response?.status===503)return "The backend or evidence corpus is currently unavailable.";
  if(error.response?.status===502)return "The Java backend could not reach the AI service.";
  if(!error.response)return "Cannot connect to the SATYA backend. Make sure Spring Boot is running.";
  const d=error.response.data?.message||error.response.data?.detail;return typeof d==="string"?d:"The server could not process this request.";
 }
 return "Something unexpected happened. Please try again.";
}