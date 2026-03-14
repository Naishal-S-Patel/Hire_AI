import { useState, useEffect } from "react";
import { Mail, Database, CheckCircle, AlertCircle, RefreshCw, Info, Link2, Loader2 } from "lucide-react";
import { connectGmail, fetchGmailResumes } from "../services/api";
import api from "../services/api";

const LinkedInIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
  </svg>
);

const DEFAULT_INGEST_EMAIL = "recruiting@example.com";

const IngestionPage = () => {
  const [message, setMessage] = useState(null);
  const [emailStatus, setEmailStatus] = useState(null);
  const [emailLoading, setEmailLoading] = useState(true);
  const [gmailConnecting, setGmailConnecting] = useState(false);
  const [gmailFetching, setGmailFetching] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [linkedinFetching, setLinkedinFetching] = useState(false);
  const [linkedinResult, setLinkedinResult] = useState(null);

  useEffect(() => { fetchEmailStatus(); }, []);

  const fetchEmailStatus = async () => {
    setEmailLoading(true);
    try {
      const res = await api.get("/ingest/email/status");
      setEmailStatus(res);
    } catch {
      setEmailStatus({ configured: false, status: "error", message: "Could not reach backend" });
    } finally {
      setEmailLoading(false);
    }
  };

  const showMsg = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 6000);
  };

  const handleGmailConnectAndFetch = async () => {
    try {
      setGmailConnecting(true);
      await connectGmail(DEFAULT_INGEST_EMAIL, "placeholder_token");
      showMsg("success", `Gmail ${DEFAULT_INGEST_EMAIL} connected successfully.`);
      
      setGmailConnecting(false);
      setGmailFetching(true);
      const res = await fetchGmailResumes(DEFAULT_INGEST_EMAIL);
      showMsg("success", res.message || `Fetched resumes from ${DEFAULT_INGEST_EMAIL}. Configure Gmail API credentials in .env for live ingestion.`);
    } catch {
      showMsg("error", "Failed to connect and fetch from Gmail");
    } finally {
      setGmailConnecting(false);
      setGmailFetching(false);
    }
  };

  const handleLinkedInFetch = async () => {
    if (!linkedinUrl.trim()) { showMsg("error", "Enter a LinkedIn profile URL first"); return; }
    if (!linkedinUrl.includes("linkedin.com")) { showMsg("error", "Please enter a valid LinkedIn URL"); return; }
    try {
      setLinkedinFetching(true);
      const res = await api.post("/ingest/linkedin/profile", { url: linkedinUrl });
      setLinkedinResult(res);
      showMsg("success", res.message || "LinkedIn profile fetched and imported successfully");
    } catch (err) {
      showMsg("error", err.response?.data?.detail || "Failed to fetch LinkedIn profile");
    } finally {
      setLinkedinFetching(false);
    }
  };

  const msgColors = {
    success: "bg-green-500/10 border-green-500/20 text-green-400",
    error: "bg-red-500/10 border-red-500/20 text-red-400",
    info: "bg-blue-500/10 border-blue-500/20 text-blue-400",
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Ingestion Management</h1>
        <p className="text-gray-400 mt-1">Connect sources to automatically import candidates into your pool.</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg border flex items-center gap-3 ${msgColors[message.type]}`}>
          {message.type === "success" ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      <div className={`p-4 rounded-xl border flex items-start gap-3 ${emailStatus?.configured ? "bg-green-500/10 border-green-500/20" : "bg-yellow-500/10 border-yellow-500/20"}`}>
        <Mail size={18} className={`mt-0.5 ${emailStatus?.configured ? "text-green-400" : "text-yellow-400"}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-sm font-semibold ${emailStatus?.configured ? "text-green-400" : "text-yellow-400"}`}>
              Background Email Ingestion
            </span>
            {emailLoading && <RefreshCw size={12} className="text-gray-400 animate-spin" />}
            {emailStatus?.configured && (
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">Active</span>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-0.5">{emailStatus?.message || "Checking status..."}</p>
        </div>
        <button onClick={fetchEmailStatus} title="Refresh" className="text-gray-500 hover:text-gray-300 transition-colors shrink-0">
          <RefreshCw size={14} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

        {/* Gmail Connect */}
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-5 flex flex-col hover:border-red-500/50 transition-colors">
          <div className="w-12 h-12 bg-red-500/20 text-red-400 rounded-xl flex items-center justify-center mb-4">
            <Mail className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white mb-1">Connect Gmail</h3>
          <p className="text-xs text-gray-400 mb-3 flex-1">Scan inbox for resume attachments and auto-import candidates.</p>
          
          <div className="bg-[#0a0f1e] border border-gray-600 rounded-lg px-3 py-2.5 mb-3 flex items-center gap-2">
            <Mail size={14} className="text-red-400 shrink-0" />
            <span className="text-sm text-gray-300 font-medium">{DEFAULT_INGEST_EMAIL}</span>
            <span className="text-xs text-green-400 ml-auto">Connected</span>
          </div>

          <button 
            onClick={handleGmailConnectAndFetch} 
            disabled={gmailConnecting || gmailFetching}
            className="w-full bg-red-600 hover:bg-red-700 text-white text-xs font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {gmailConnecting || gmailFetching ? (
              <><Loader2 size={14} className="animate-spin" />{gmailConnecting ? "Connecting..." : "Fetching..."}</>
            ) : (
              "Connect & Fetch Resumes"
            )}
          </button>
        </div>

        {/* LinkedIn Profile URL Import */}
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-5 flex flex-col hover:border-blue-500/50 transition-colors">
          <div className="w-12 h-12 bg-blue-500/20 text-blue-400 rounded-xl flex items-center justify-center mb-4">
            <LinkedInIcon />
          </div>
          <h3 className="text-base font-bold text-white mb-1">LinkedIn Import</h3>
          <p className="text-xs text-gray-400 mb-3 flex-1">Enter a LinkedIn profile URL to fetch and import candidate details.</p>
          
          <div className="relative mb-3">
            <Link2 size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="url"
              placeholder="https://linkedin.com/in/username"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              className="w-full bg-[#0a0f1e] border border-gray-600 text-gray-300 text-xs rounded-lg pl-9 pr-3 py-2.5 focus:outline-none focus:border-blue-500"
            />
          </div>

          <button 
            onClick={handleLinkedInFetch}
            disabled={linkedinFetching}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {linkedinFetching ? (
              <><Loader2 size={14} className="animate-spin" />Fetching Profile...</>
            ) : (
              "Fetch Profile"
            )}
          </button>

          {linkedinResult && linkedinResult.details?.candidate && (
            <div className="mt-3 bg-[#0a0f1e] border border-green-500/30 rounded-lg p-3 space-y-1">
              <p className="text-xs text-green-400 font-semibold">Profile Imported!</p>
              <p className="text-xs text-gray-300">{linkedinResult.details.candidate.name}</p>
              <p className="text-xs text-gray-500">{linkedinResult.details.candidate.role}</p>
            </div>
          )}
        </div>

        {/* HRMS Sync */}
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-5 flex flex-col hover:border-purple-500/50 transition-colors">
          <div className="w-12 h-12 bg-purple-500/20 text-purple-400 rounded-xl flex items-center justify-center mb-4">
            <Database className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white mb-1">HRMS Sync</h3>
          <p className="text-xs text-gray-400 mb-4 flex-1">Sync candidates from Workday, BambooHR, or other HRMS platforms.</p>
          <button onClick={() => showMsg("info", "Configure HRMS_URL and HRMS_API_KEY in backend/.env to activate.")}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium py-2.5 rounded-lg transition-colors flex justify-center items-center mt-auto">
            <Database className="w-3.5 h-3.5 mr-1.5" /> Configure Sync
          </button>
        </div>

      </div>

      <div className="bg-[#1a2332] border border-gray-700 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Recent Activity</h3>
          <span className="text-xs text-gray-500">Updates after each action</span>
        </div>
        <div className="p-6 flex items-center justify-center text-gray-500 text-sm">
          No recent ingestion activity. Upload a file or connect a source above.
        </div>
      </div>
    </div>
  );
};

export default IngestionPage;