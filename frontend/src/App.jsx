// import { useState, useRef, useEffect, useCallback } from "react";
// import axios from "axios";
// import {
//   BarChart, Bar, LineChart, Line,
//   XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Area, AreaChart
// } from "recharts";

// // ─── Fonts ────────────────────────────────────────────────────────────────────
// const fontLink = document.createElement("link");
// fontLink.rel = "stylesheet";
// fontLink.href = "https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap";
// document.head.appendChild(fontLink);

// // ─── Global Styles ────────────────────────────────────────────────────────────
// const style = document.createElement("style");
// style.textContent = `
//   *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
//   body { font-family: 'Sora', sans-serif; background: #F5F4FF; color: #1a1535; }

//   :root {
//     --purple: #7C3AED;
//     --purple-light: #EDE9FE;
//     --orange: #F97316;
//     --gradient: linear-gradient(135deg, #7C3AED 0%, #F97316 100%);
//     --white: #FFFFFF;
//     --gray-50: #F9F8FF;
//     --gray-100: #F0EEFF;
//     --gray-200: #E4E0FA;
//     --gray-400: #9CA3AF;
//     --gray-500: #6B7280;
//     --gray-800: #1F2937;
//     --shadow-sm: 0 1px 3px rgba(124,58,237,0.08), 0 1px 2px rgba(0,0,0,0.04);
//     --shadow-md: 0 4px 16px rgba(124,58,237,0.1), 0 2px 6px rgba(0,0,0,0.06);
//     --shadow-lg: 0 10px 40px rgba(124,58,237,0.15), 0 4px 12px rgba(0,0,0,0.08);
//     --radius: 16px;
//     --radius-sm: 10px;
//     --radius-xs: 6px;
//   }

//   .ds-root {
//     min-height: 100vh;
//     display: flex;
//     flex-direction: column;
//     background: #F5F4FF;
//   }

//   /* ── Navbar ── */
//   .ds-nav {
//     position: sticky; top: 0; z-index: 100;
//     height: 60px;
//     background: rgba(255,255,255,0.85);
//     backdrop-filter: blur(12px);
//     border-bottom: 1px solid var(--gray-200);
//     display: flex; align-items: center; justify-content: space-between;
//     padding: 0 32px;
//   }
//   .ds-logo {
//     font-size: 20px; font-weight: 700; letter-spacing: -0.5px;
//     background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
//     background-clip: text;
//   }
//   .ds-nav-right { display: flex; align-items: center; gap: 16px; }
//   .ds-nav-pill {
//     display: flex; align-items: center; gap: 8px;
//     padding: 6px 14px;
//     background: var(--gray-100); border-radius: 999px;
//     font-size: 13px; color: var(--gray-500); font-weight: 500;
//     border: 1px solid var(--gray-200);
//     cursor: pointer; transition: all 0.2s;
//     font-family: 'DM Mono', monospace;
//   }
//   .ds-nav-pill svg { flex-shrink: 0; }
//   .ds-nav-pill:hover { background: var(--purple-light); color: var(--purple); border-color: var(--purple); }
//   .ds-nav-icon {
//     width: 36px; height: 36px; border-radius: 50%;
//     background: var(--gray-100); border: 1px solid var(--gray-200);
//     display: flex; align-items: center; justify-content: center;
//     cursor: pointer; transition: all 0.2s; color: var(--gray-500);
//   }
//   .ds-nav-icon:hover { background: var(--purple-light); color: var(--purple); }
//   .ds-download-btn {
//     display: flex; align-items: center; gap: 6px;
//     padding: 8px 16px;
//     background: var(--gray-100); border-radius: 10px;
//     font-size: 13px; color: var(--gray-800); font-weight: 600;
//     border: 1px solid var(--gray-200);
//     cursor: pointer; transition: all 0.2s;
//   }
//   .ds-download-btn:hover { background: var(--purple-light); color: var(--purple); border-color: var(--purple); }

//   /* ── Main ── */
//   .ds-main {
//     flex: 1;
//     display: flex; flex-direction: column;
//     max-width: 860px; width: 100%;
//     margin: 0 auto;
//     padding: 0 24px;
//   }

//   /* ── Landing ── */
//   .ds-landing {
//     display: flex; flex-direction: column; align-items: center;
//     padding: 72px 0 200px;
//     animation: fadeUp 0.6s ease both;
//   }
//   @keyframes fadeUp {
//     from { opacity: 0; transform: translateY(24px); }
//     to { opacity: 1; transform: translateY(0); }
//   }
//   .ds-headline {
//     font-size: clamp(28px, 5vw, 48px);
//     font-weight: 700; text-align: center;
//     line-height: 1.2; letter-spacing: -1.5px;
//     color: var(--gray-800);
//     max-width: 600px;
//   }
//   .ds-headline-accent {
//     background: var(--gradient);
//     -webkit-background-clip: text; -webkit-text-fill-color: transparent;
//     background-clip: text;
//   }
//   .ds-subtext {
//     margin-top: 16px;
//     font-size: 16px; color: var(--gray-500);
//     text-align: center; max-width: 480px;
//     line-height: 1.6;
//   }

//   /* ── Drop Zone ── */
//   .ds-dropzone {
//     margin-top: 40px;
//     width: 100%; max-width: 620px;
//     border: 2px dashed var(--gray-200);
//     border-radius: 20px;
//     background: var(--white);
//     padding: 56px 32px;
//     display: flex; flex-direction: column; align-items: center;
//     cursor: pointer; transition: all 0.25s;
//     position: relative; overflow: hidden;
//   }
//   .ds-dropzone::before {
//     content: '';
//     position: absolute; inset: 0;
//     background: linear-gradient(135deg, rgba(124,58,237,0.03), rgba(249,115,22,0.03));
//     opacity: 0; transition: opacity 0.25s;
//   }
//   .ds-dropzone:hover { border-color: var(--purple); box-shadow: var(--shadow-lg); }
//   .ds-dropzone:hover::before { opacity: 1; }
//   .ds-dropzone.active { border-color: var(--purple); background: var(--purple-light); }
//   .ds-drop-icon {
//     width: 60px; height: 60px; border-radius: 50%;
//     background: var(--gray-100);
//     display: flex; align-items: center; justify-content: center;
//     margin-bottom: 18px; color: var(--purple);
//     transition: all 0.25s;
//   }
//   .ds-dropzone:hover .ds-drop-icon { background: var(--purple-light); transform: scale(1.08); }
//   .ds-drop-title { font-size: 18px; font-weight: 600; color: var(--gray-800); }
//   .ds-drop-sub { font-size: 14px; color: var(--gray-400); margin-top: 6px; }
//   .ds-drop-sub span { color: var(--purple); font-weight: 500; }
//   .ds-hidden-input { display: none; }
//   .ds-sparkle-icon {
//     position: absolute; top: 16px; right: 16px;
//     width: 40px; height: 40px;
//     background: var(--gray-100); border-radius: 50%;
//     display: flex; align-items: center; justify-content: center;
//     color: var(--gray-400);
//   }

//   /* ── Examples ── */
//   .ds-examples-label {
//     margin-top: 32px;
//     font-size: 11px; font-weight: 600; letter-spacing: 2px;
//     text-transform: uppercase; color: var(--gray-400);
//   }
//   .ds-examples { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; justify-content: center; }
//   .ds-example-chip {
//     padding: 8px 18px;
//     border: 1px solid var(--gray-200);
//     border-radius: 999px; background: var(--white);
//     font-size: 13px; color: var(--gray-500);
//     cursor: pointer; transition: all 0.2s;
//   }
//   .ds-example-chip:hover { border-color: var(--purple); color: var(--purple); background: var(--purple-light); }

//   /* ── Chat ── */
//   .ds-chat {
//     flex: 1; padding: 32px 0 220px;
//     display: flex; flex-direction: column; gap: 28px;
//     animation: fadeUp 0.4s ease both;
//   }

//   /* Welcome message */
//   .ds-msg { display: flex; flex-direction: column; gap: 4px; }
//   .ds-msg-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
//   .ds-avatar {
//     width: 36px; height: 36px; border-radius: 50%;
//     background: var(--gradient);
//     display: flex; align-items: center; justify-content: center;
//     flex-shrink: 0;
//   }
//   .ds-msg-name { font-size: 14px; font-weight: 600; color: var(--gray-800); }
//   .ds-msg-sub { font-size: 12px; color: var(--gray-400); }
//   .ds-welcome-card {
//     background: var(--white);
//     border-radius: var(--radius);
//     padding: 20px 24px;
//     box-shadow: var(--shadow-sm);
//     border: 1px solid var(--gray-200);
//   }
//   .ds-welcome-title { font-size: 15px; font-weight: 600; color: var(--gray-800); margin-bottom: 4px; }
//   .ds-welcome-sub { font-size: 14px; color: var(--gray-500); line-height: 1.5; }

//   /* User bubble */
//   .ds-user-row { display: flex; justify-content: flex-end; }
//   .ds-user-bubble {
//     max-width: 70%;
//     padding: 10px 16px;
//     background: var(--gray-100);
//     border: 1px solid var(--gray-200);
//     border-radius: 14px 14px 4px 14px;
//     font-size: 14px; color: var(--gray-800);
//     font-weight: 500;
//   }

//   /* Response card */
//   .ds-response-card {
//     background: var(--white);
//     border-radius: var(--radius);
//     overflow: hidden;
//     box-shadow: var(--shadow-sm);
//     border: 1px solid var(--gray-200);
//   }
//   .ds-response-body { padding: 24px; }
//   .ds-response-title { font-size: 16px; font-weight: 700; color: var(--gray-800); letter-spacing: -0.3px; }
//   .ds-response-desc { font-size: 14px; color: var(--gray-500); margin-top: 6px; line-height: 1.6; }

//   /* Insight */
//   .ds-insight {
//     margin-top: 16px;
//     padding: 14px 16px;
//     background: var(--gray-50);
//     border-left: 3px solid var(--orange);
//     border-radius: 0 8px 8px 0;
//   }
//   .ds-insight-header {
//     display: flex; align-items: center; gap: 6px;
//     font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
//     text-transform: uppercase; color: var(--orange);
//     margin-bottom: 8px;
//   }
//   .ds-insight p { font-size: 14px; color: var(--gray-800); line-height: 1.6; margin-bottom: 4px; }

//   /* Table */
//   .ds-table-wrap { margin-top: 16px; overflow-x: auto; }
//   .ds-table { width: 100%; border-collapse: collapse; font-size: 13px; }
//   .ds-table th {
//     background: var(--gray-50); color: var(--gray-500);
//     font-weight: 600; font-size: 11px; text-transform: uppercase;
//     letter-spacing: 0.8px; padding: 10px 12px;
//     border-bottom: 1px solid var(--gray-200); text-align: left;
//   }
//   .ds-table td {
//     padding: 10px 12px; border-bottom: 1px solid var(--gray-200);
//     color: var(--gray-800); font-family: 'DM Mono', monospace;
//   }
//   .ds-table tr:last-child td { border-bottom: none; }
//   .ds-table tr:hover td { background: var(--gray-50); }

//   /* Chart area */
//   .ds-chart-area {
//     padding: 0 24px 24px;
//     background: var(--white);
//   }
//   .ds-chart-label { font-size: 12px; color: var(--gray-400); margin-bottom: 4px; font-weight: 500; }
//   .ds-chart-unit { font-size: 11px; color: var(--gray-400); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }

//   /* Suggestion chips inside chat */
//   .ds-chips { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 24px 20px; }
//   .ds-chip {
//     padding: 7px 16px;
//     border: 1px solid var(--gray-200); border-radius: 999px;
//     font-size: 13px; color: var(--gray-500);
//     cursor: pointer; background: var(--white);
//     transition: all 0.2s;
//   }
//   .ds-chip:hover { border-color: var(--purple); color: var(--purple); background: var(--purple-light); }

//   /* ── Sticky Input ── */
//   .ds-input-bar {
//     position: fixed; bottom: 0; left: 0; right: 0;
//     background: rgba(255,255,255,0.92);
//     backdrop-filter: blur(16px);
//     border-top: 1px solid var(--gray-200);
//     padding: 14px 24px 18px;
//     display: flex; flex-direction: column; align-items: center; gap: 10px;
//     z-index: 50;
//   }
//   .ds-input-inner {
//     width: 100%; max-width: 812px;
//     display: flex; gap: 0;
//     background: var(--white);
//     border: 1.5px solid var(--gray-200);
//     border-radius: 14px;
//     overflow: hidden;
//     transition: border-color 0.2s, box-shadow 0.2s;
//   }
//   .ds-input-inner:focus-within {
//     border-color: var(--purple);
//     box-shadow: 0 0 0 4px rgba(124,58,237,0.08);
//   }
//   .ds-input-attach {
//     display: flex; align-items: center; padding: 0 12px;
//     color: var(--gray-400); cursor: pointer;
//     transition: color 0.2s;
//   }
//   .ds-input-attach:hover { color: var(--purple); }
//   .ds-input-field {
//     flex: 1; padding: 14px 8px;
//     font-size: 15px; font-family: 'Sora', sans-serif;
//     border: none; outline: none; background: transparent;
//     color: var(--gray-800);
//   }
//   .ds-input-field::placeholder { color: var(--gray-400); }
//   .ds-send-btn {
//     margin: 6px; width: 40px; height: 40px;
//     border-radius: 10px;
//     background: var(--gradient);
//     border: none; cursor: pointer;
//     display: flex; align-items: center; justify-content: center;
//     color: white; transition: all 0.2s;
//     flex-shrink: 0;
//   }
//   .ds-send-btn:hover { opacity: 0.88; transform: scale(1.04); }
//   .ds-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

//   /* ── Suggestions in bar ── */
//   .ds-bar-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 812px; width: 100%; }
//   .ds-bar-chip {
//     padding: 6px 14px;
//     border: 1px solid var(--gray-200); border-radius: 999px;
//     font-size: 12.5px; color: var(--gray-500);
//     cursor: pointer; background: var(--white);
//     transition: all 0.2s;
//   }
//   .ds-bar-chip:hover { border-color: var(--purple); color: var(--purple); background: var(--purple-light); }

//   /* ── Loading ── */
//   .ds-loading {
//     display: flex; align-items: center; gap: 10px;
//     padding: 16px 20px;
//     background: var(--white); border-radius: var(--radius);
//     border: 1px solid var(--gray-200);
//   }
//   .ds-dots { display: flex; gap: 5px; }
//   .ds-dot {
//     width: 7px; height: 7px; border-radius: 50%;
//     background: var(--purple);
//     animation: bounce 1.2s infinite ease-in-out;
//   }
//   .ds-dot:nth-child(2) { animation-delay: 0.2s; background: #9B59D9; }
//   .ds-dot:nth-child(3) { animation-delay: 0.4s; background: var(--orange); }
//   @keyframes bounce {
//     0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
//     40% { transform: scale(1); opacity: 1; }
//   }
//   .ds-loading-text { font-size: 14px; color: var(--gray-500); }

//   /* ── Footer ── */
//   .ds-footer {
//     text-align: center; padding: 16px;
//     font-size: 11px; color: var(--gray-400); letter-spacing: 0.5px;
//     text-transform: uppercase;
//     border-top: 1px solid var(--gray-200);
//     background: var(--white);
//   }
//   .ds-footer a { color: var(--gray-400); text-decoration: none; margin: 0 10px; }
//   .ds-footer a:hover { color: var(--purple); }

//   /* Custom tooltip for recharts */
//   .custom-tooltip {
//     background: var(--white); border: 1px solid var(--gray-200);
//     border-radius: 8px; padding: 10px 14px;
//     box-shadow: var(--shadow-md);
//     font-family: 'Sora', sans-serif; font-size: 13px;
//   }
// `;
// document.head.appendChild(style);

// // ─── Icons ────────────────────────────────────────────────────────────────────
// const Icon = {
//   Upload: () => (
//     <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
//     </svg>
//   ),
//   Sparkle: () => (
//     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
//     </svg>
//   ),
//   Bell: () => (
//     <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
//     </svg>
//   ),
//   User: () => (
//     <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z" />
//     </svg>
//   ),
//   Download: () => (
//     <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
//     </svg>
//   ),
//   Attach: () => (
//     <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
//     </svg>
//   ),
//   Chart: () => (
//     <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
//     </svg>
//   ),
//   File: () => (
//     <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
//     </svg>
//   ),
//   Send: () => (
//     <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.269 20.876L5.999 12zm0 0h7.5" />
//     </svg>
//   ),
//   Bulb: () => (
//     <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
//       <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
//     </svg>
//   ),
// };

// // ─── Custom Tooltip ────────────────────────────────────────────────────────────
// const CustomTooltip = ({ active, payload, label }) => {
//   if (active && payload?.length) {
//     return (
//       <div className="custom-tooltip">
//         <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
//         <div style={{ color: "#7C3AED" }}>{payload[0].value?.toLocaleString()}</div>
//       </div>
//     );
//   }
//   return null;
// };

// // ─── Sparkle Avatar ───────────────────────────────────────────────────────────
// const SparkleAvatar = () => (
//   <div className="ds-avatar">
//     <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
//       <path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
//     </svg>
//   </div>
// );

// // ─── App ──────────────────────────────────────────────────────────────────────
// export default function App() {
//   const [file, setFile] = useState(null);
//   const [uploadedInfo, setUploadedInfo] = useState(null); // { name, rows, columns, suggestions }
//   const [query, setQuery] = useState("");
//   const [chatHistory, setChatHistory] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [dragOver, setDragOver] = useState(false);

//   const bottomRef = useRef(null);
//   const fileRef = useRef(null);
//   const inputRef = useRef(null);

//   useEffect(() => {
//     bottomRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [chatHistory, loading]);

//   const EXAMPLE_QUERIES = [
//     '"Top 5 products by revenue"',
//     '"Show sales trends over time"',
//     '"Find most sold product"',
//     '"Revenue by region"',
//   ];

//   const SUGGESTIONS = uploadedInfo?.suggestions || [
//     "Top 5 by revenue",
//     "Show trends over time",
//     "Distribution by category",
//     "Find anomalies",
//   ];

//   // ── Upload ──
//   const handleUpload = async (f) => {
//     const fileToUpload = f || file;
//     if (!fileToUpload) return;

//     const formData = new FormData();
//     formData.append("file", fileToUpload);

//     try {
//       const res = await axios.post("http://127.0.0.1:8000/api/upload", formData);
//       setUploadedInfo({
//         name: fileToUpload.name,
//         rows: res.data.rows,
//         columns: res.data.columns,
//         suggestions: res.data.suggestions,
//       });
//     } catch (err) {
//       // For demo/dev: show upload worked anyway
//       setUploadedInfo({
//         name: fileToUpload.name,
//         rows: "—",
//         columns: [],
//         suggestions: null,
//       });
//     }
//   };

//   const onFileChange = (e) => {
//     const f = e.target.files[0];
//     if (f) { setFile(f); handleUpload(f); }
//   };

//   const onDrop = useCallback((e) => {
//     e.preventDefault(); setDragOver(false);
//     const f = e.dataTransfer.files[0];
//     if (f) { setFile(f); handleUpload(f); }
//   }, []);

//   // ── Query ──
//   const handleQuery = async (customQuery = null) => {
//     const q = customQuery || query;
//     if (!q || loading) return;

//     setLoading(true);
//     setQuery("");

//     try {
//       const res = await axios.post("http://127.0.0.1:8000/api/query", { query: q });
//       setChatHistory((prev) => [...prev, { query: q, response: res.data }]);
//     } catch (err) {
//       setChatHistory((prev) => [...prev, {
//         query: q,
//         response: {
//           title: "Analysis Result",
//           description: "Here's what I found in your dataset.",
//           insight: "The data shows interesting patterns worth exploring further.",
//         }
//       }]);
//     }

//     setLoading(false);
//   };

//   // ── Export ──
//   const handleExport = async () => {
//     try {
//       const res = await axios.post(
//         "http://127.0.0.1:8000/api/export",
//         { chatHistory },
//         { responseType: "blob" }
//       );
//       const url = window.URL.createObjectURL(new Blob([res.data]));
//       const link = document.createElement("a");
//       link.href = url;
//       link.setAttribute("download", "DataSage_Report.pdf");
//       document.body.appendChild(link);
//       link.click();
//     } catch (err) {
//       console.error(err);
//     }
//   };

//   const hasUploaded = !!uploadedInfo;

//   return (
//     <div className="ds-root">

//       {/* ── Navbar ── */}
//       <nav className="ds-nav">
//         <div className="ds-logo">DataSage</div>
//         <div className="ds-nav-right">
//           {hasUploaded && (
//             <>
//               <div className="ds-nav-pill">
//                 <Icon.File />
//                 {uploadedInfo.name}
//                 {uploadedInfo.rows !== "—" && <span style={{ color: "#9CA3AF" }}>({uploadedInfo.rows?.toLocaleString()} rows)</span>}
//               </div>
//               <button className="ds-download-btn" onClick={handleExport}>
//                 <Icon.Download /> Download Report
//               </button>
//             </>
//           )}
//           <div className="ds-nav-icon"><Icon.Bell /></div>
//           <div className="ds-nav-icon"><Icon.User /></div>
//         </div>
//       </nav>

//       {/* ── Main ── */}
//       <div className="ds-main">

//         {/* ── Landing ── */}
//         {!hasUploaded && (
//           <div className="ds-landing">
//             <h1 className="ds-headline">
//               Upload your dataset to unlock{" "}
//               <span className="ds-headline-accent">intelligent insights</span>
//             </h1>
//             <p className="ds-subtext">
//               Analyze your data using natural language. Generate charts, summaries, and insights instantly with our AI-driven analytics suite.
//             </p>

//             {/* Drop zone */}
//             <div
//               className={`ds-dropzone ${dragOver ? "active" : ""}`}
//               onClick={() => fileRef.current?.click()}
//               onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
//               onDragLeave={() => setDragOver(false)}
//               onDrop={onDrop}
//             >
//               <div className="ds-sparkle-icon"><Icon.Sparkle /></div>
//               <div className="ds-drop-icon"><Icon.Upload /></div>
//               <div className="ds-drop-title">Drop your dataset here</div>
//               <div className="ds-drop-sub">or browse <span>(CSV, XLSX supported)</span></div>
//               <input
//                 ref={fileRef}
//                 type="file"
//                 accept=".csv,.xlsx,.xls"
//                 className="ds-hidden-input"
//                 onChange={onFileChange}
//               />
//             </div>

//             <p className="ds-examples-label">Try these examples</p>
//             <div className="ds-examples">
//               {EXAMPLE_QUERIES.map((q, i) => (
//                 <div key={i} className="ds-example-chip">{q}</div>
//               ))}
//             </div>
//           </div>
//         )}

//         {/* ── Chat view ── */}
//         {hasUploaded && (
//           <div className="ds-chat">

//             {/* Welcome */}
//             <div className="ds-msg">
//               <div className="ds-msg-header">
//                 <SparkleAvatar />
//                 <div>
//                   <div className="ds-msg-name">DataSage</div>
//                   <div className="ds-msg-sub">AI Analyst</div>
//                 </div>
//               </div>
//               <div className="ds-welcome-card">
//                 <div className="ds-welcome-title">Welcome to your analyst workspace.</div>
//                 <div className="ds-welcome-sub">Your dataset is ready. Ask anything to analyze, visualize, or summarize your data.</div>
//               </div>
//             </div>

//             {/* Chat history */}
//             {chatHistory.map((chat, i) => (
//               <div key={i} style={{ display: "flex", flexDirection: "column", gap: 12 }}>

//                 {/* User bubble */}
//                 <div className="ds-user-row">
//                   <div className="ds-user-bubble">{chat.query}</div>
//                 </div>

//                 {/* Response */}
//                 <div className="ds-msg">
//                   <div className="ds-msg-header">
//                     <SparkleAvatar />
//                     <div>
//                       <div className="ds-msg-name">DataSage</div>
//                       <div className="ds-msg-sub">AI Analyst</div>
//                     </div>
//                   </div>
//                   <div className="ds-response-card">
//                     <div className="ds-response-body">
//                       <div className="ds-response-title">{chat.response.title}</div>
//                       {chat.response.description && (
//                         <div className="ds-response-desc">{chat.response.description}</div>
//                       )}

//                       {/* Insight */}
//                       {chat.response.insight && (
//                         <div className="ds-insight">
//                           <div className="ds-insight-header">
//                             <Icon.Bulb /> Key Insight
//                           </div>
//                           {chat.response.insight.split("\n").map((line, idx) => (
//                             <p key={idx}>{line.replace(/\*\*/g, "")}</p>
//                           ))}
//                         </div>
//                       )}

//                       {/* Table */}
//                       {chat.response.table?.length > 0 && (
//                         <div className="ds-table-wrap">
//                           <table className="ds-table">
//                             <thead>
//                               <tr>
//                                 {Object.keys(chat.response.table[0]).map((k) => (
//                                   <th key={k}>{k}</th>
//                                 ))}
//                               </tr>
//                             </thead>
//                             <tbody>
//                               {chat.response.table.map((row, idx) => (
//                                 <tr key={idx}>
//                                   {Object.values(row).map((v, j) => (
//                                     <td key={j}>{v}</td>
//                                   ))}
//                                 </tr>
//                               ))}
//                             </tbody>
//                           </table>
//                         </div>
//                       )}
//                     </div>

//                     {/* Chart */}
//                     {chat.response.chart && (
//                       <div className="ds-chart-area">
//                         <div className="ds-chart-label">Monthly Performance</div>
//                         <div className="ds-chart-unit">USD in Millions</div>
//                         <ResponsiveContainer width="100%" height={220}>
//                           {chat.response.chart.type === "line" ? (
//                             <AreaChart data={chat.response.chart.labels.map((l, i) => ({
//                               name: l, value: chat.response.chart.values[i]
//                             }))}>
//                               <defs>
//                                 <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
//                                   <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.15} />
//                                   <stop offset="95%" stopColor="#7C3AED" stopOpacity={0} />
//                                 </linearGradient>
//                               </defs>
//                               <CartesianGrid strokeDasharray="3 3" stroke="#F0EEFF" />
//                               <XAxis dataKey="name" tick={{ fontSize: 12, fontFamily: "Sora", fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
//                               <YAxis tick={{ fontSize: 12, fontFamily: "Sora", fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
//                               <Tooltip content={<CustomTooltip />} />
//                               <Area type="monotone" dataKey="value" stroke="#7C3AED" strokeWidth={2.5} fill="url(#colorVal)" dot={{ fill: "#7C3AED", r: 4 }} />
//                             </AreaChart>
//                           ) : (
//                             <BarChart data={chat.response.chart.labels.map((l, i) => ({
//                               name: l, value: chat.response.chart.values[i]
//                             }))}>
//                               <CartesianGrid strokeDasharray="3 3" stroke="#F0EEFF" vertical={false} />
//                               <XAxis dataKey="name" tick={{ fontSize: 12, fontFamily: "Sora", fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
//                               <YAxis tick={{ fontSize: 12, fontFamily: "Sora", fill: "#9CA3AF" }} axisLine={false} tickLine={false} />
//                               <Tooltip content={<CustomTooltip />} />
//                               <Bar dataKey="value" fill="#7C3AED" radius={[6, 6, 0, 0]} />
//                             </BarChart>
//                           )}
//                         </ResponsiveContainer>
//                       </div>
//                     )}

//                     {/* Chips below chart */}
//                     <div className="ds-chips">
//                       {SUGGESTIONS.map((s, i) => (
//                         <div key={i} className="ds-chip" onClick={() => handleQuery(s)}>{s}</div>
//                       ))}
//                     </div>
//                   </div>
//                 </div>
//               </div>
//             ))}

//             {/* Loading */}
//             {loading && (
//               <div className="ds-loading">
//                 <div className="ds-dots">
//                   <div className="ds-dot" />
//                   <div className="ds-dot" />
//                   <div className="ds-dot" />
//                 </div>
//                 <div className="ds-loading-text">Analyzing your dataset…</div>
//               </div>
//             )}

//             <div ref={bottomRef} />
//           </div>
//         )}
//       </div>

//       {/* ── Sticky Input ── */}
//       <div className="ds-input-bar">
//         {hasUploaded && (
//           <div className="ds-bar-chips">
//             {SUGGESTIONS.map((s, i) => (
//               <div key={i} className="ds-bar-chip" onClick={() => handleQuery(s)}>{s}</div>
//             ))}
//           </div>
//         )}
//         <div className="ds-input-inner">
//           <label className="ds-input-attach" htmlFor="inline-file">
//             <Icon.Attach />
//             <input id="inline-file" type="file" accept=".csv,.xlsx,.xls" className="ds-hidden-input" onChange={onFileChange} />
//           </label>
//           <div className="ds-input-attach" style={{ cursor: "default" }}>
//             <Icon.Chart />
//           </div>
//           <input
//             ref={inputRef}
//             className="ds-input-field"
//             placeholder="Ask something about your dataset..."
//             value={query}
//             onChange={(e) => setQuery(e.target.value)}
//             onKeyDown={(e) => e.key === "Enter" && handleQuery()}
//           />
//           <button
//             className="ds-send-btn"
//             onClick={() => handleQuery()}
//             disabled={loading || !query.trim()}
//           >
//             <Icon.Send />
//           </button>
//         </div>
//       </div>

//       {/* ── Footer ── */}
//       <footer className="ds-footer" style={{ paddingBottom: 180 }}>
//         <a href="#">Documentation</a>
//         <a href="#">Privacy Policy</a>
//         <a href="#">API Support</a>
//         <br />
//         <span style={{ marginTop: 6, display: "block" }}>© 2024 DataSage AI. Powered by Advanced Analytics.</span>
//       </footer>

//     </div>
//   );
// }


import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Area, AreaChart
} from "recharts";

// ─── Fonts ────────────────────────────────────────────────────────────────────
const fontLink = document.createElement("link");
fontLink.rel = "stylesheet";
fontLink.href = "https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap";
document.head.appendChild(fontLink);

// ─── Global Styles ────────────────────────────────────────────────────────────
const style = document.createElement("style");
style.textContent = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Sora', sans-serif; background: #F5F4FF; color: #1a1535; }

  :root {
    --purple: #7C3AED;
    --purple-light: #EDE9FE;
    --orange: #F97316;
    --gradient: linear-gradient(135deg, #7C3AED 0%, #F97316 100%);
    --white: #FFFFFF;
    --gray-50: #F9F8FF;
    --gray-100: #F0EEFF;
    --gray-200: #E4E0FA;
    --gray-400: #9CA3AF;
    --gray-500: #6B7280;
    --gray-800: #1F2937;
    --shadow-sm: 0 1px 3px rgba(124,58,237,0.08), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 16px rgba(124,58,237,0.1), 0 2px 6px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 40px rgba(124,58,237,0.15), 0 4px 12px rgba(0,0,0,0.08);
    --radius: 16px;
    --radius-sm: 10px;
    --radius-xs: 6px;
  }

  .ds-root {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: #F5F4FF;
  }

  /* ── Navbar ── */
  .ds-nav {
    position: sticky; top: 0; z-index: 100;
    height: 60px;
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--gray-200);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 32px;
  }
  .ds-logo {
    font-size: 20px; font-weight: 700; letter-spacing: -0.5px;
    background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .ds-nav-right { display: flex; align-items: center; gap: 16px; }
  .ds-nav-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 14px;
    background: var(--gray-100); border-radius: 999px;
    font-size: 13px; color: var(--gray-500); font-weight: 500;
    border: 1px solid var(--gray-200);
    cursor: pointer; transition: all 0.2s;
    font-family: 'DM Mono', monospace;
  }
  .ds-nav-pill svg { flex-shrink: 0; }
  .ds-nav-pill:hover { background: var(--purple-light); color: var(--purple); border-color: var(--purple); }
  .ds-nav-icon {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--gray-100); border: 1px solid var(--gray-200);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: all 0.2s; color: var(--gray-500);
  }
  .ds-nav-icon:hover { background: var(--purple-light); color: var(--purple); }
  .ds-download-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 8px 16px;
    background: var(--gray-100); border-radius: 10px;
    font-size: 13px; color: var(--gray-800); font-weight: 600;
    border: 1px solid var(--gray-200);
    cursor: pointer; transition: all 0.2s;
  }
  .ds-download-btn:hover { background: var(--purple-light); color: var(--purple); border-color: var(--purple); }

  /* ── Main ── */
  .ds-main {
    flex: 1;
    display: flex; flex-direction: column;
    max-width: 860px; width: 100%;
    margin: 0 auto;
    padding: 0 24px;
  }

  /* ── Landing ── */
  .ds-landing {
    display: flex; flex-direction: column; align-items: center;
    padding: 72px 0 200px;
    animation: fadeUp 0.6s ease both;
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(24px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .ds-headline {
    font-size: clamp(28px, 5vw, 48px);
    font-weight: 700; text-align: center;
    line-height: 1.2; letter-spacing: -1.5px;
    color: var(--gray-800);
    max-width: 600px;
  }
  .ds-headline-accent {
    background: var(--gradient);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .ds-subtext {
    margin-top: 16px;
    font-size: 16px; color: var(--gray-500);
    text-align: center; max-width: 480px;
    line-height: 1.6;
  }

  /* ── Drop Zone ── */
  .ds-dropzone {
    margin-top: 40px;
    width: 100%; max-width: 620px;
    border: 2px dashed var(--gray-200);
    border-radius: 20px;
    background: var(--white);
    padding: 56px 32px;
    display: flex; flex-direction: column; align-items: center;
    cursor: pointer; transition: all 0.25s;
    position: relative; overflow: hidden;
  }
  .ds-dropzone::before {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(124,58,237,0.03), rgba(249,115,22,0.03));
    opacity: 0; transition: opacity 0.25s;
  }
  .ds-dropzone:hover { border-color: var(--purple); box-shadow: var(--shadow-lg); }
  .ds-dropzone:hover::before { opacity: 1; }
  .ds-dropzone.active { border-color: var(--purple); background: var(--purple-light); }
  .ds-drop-icon {
    width: 60px; height: 60px; border-radius: 50%;
    background: var(--gray-100);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 18px; color: var(--purple);
    transition: all 0.25s;
  }
  .ds-dropzone:hover .ds-drop-icon { background: var(--purple-light); transform: scale(1.08); }
  .ds-drop-title { font-size: 18px; font-weight: 600; color: var(--gray-800); }
  .ds-drop-sub { font-size: 14px; color: var(--gray-400); margin-top: 6px; }
  .ds-drop-sub span { color: var(--purple); font-weight: 500; }
  .ds-hidden-input { display: none; }
  .ds-sparkle-icon {
    position: absolute; top: 16px; right: 16px;
    width: 40px; height: 40px;
    background: var(--gray-100); border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    color: var(--gray-400);
  }

  /* ── Examples ── */
  .ds-examples-label {
    margin-top: 32px;
    font-size: 11px; font-weight: 600; letter-spacing: 2px;
    text-transform: uppercase; color: var(--gray-400);
  }
  .ds-examples { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; justify-content: center; }
  .ds-example-chip {
    padding: 8px 18px;
    border: 1px solid var(--gray-200);
    border-radius: 999px; background: var(--white);
    font-size: 13px; color: var(--gray-500);
    cursor: pointer; transition: all 0.2s;
  }
  .ds-example-chip:hover { border-color: var(--purple); color: var(--purple); background: var(--purple-light); }

  /* ── Chat ── */
  .ds-chat {
    flex: 1; padding: 32px 0 220px;
    display: flex; flex-direction: column; gap: 28px;
    animation: fadeUp 0.4s ease both;
  }

  /* Welcome message */
  .ds-msg { display: flex; flex-direction: column; gap: 4px; }
  .ds-msg-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
  .ds-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--gradient);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .ds-msg-name { font-size: 14px; font-weight: 600; color: var(--gray-800); }
  .ds-msg-sub { font-size: 12px; color: var(--gray-400); }
  .ds-welcome-card {
    background: var(--white);
    border-radius: var(--radius);
    padding: 20px 24px;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--gray-200);
  }
  .ds-welcome-title { font-size: 15px; font-weight: 600; color: var(--gray-800); margin-bottom: 4px; }
  .ds-welcome-sub { font-size: 14px; color: var(--gray-500); line-height: 1.5; }

  /* User bubble */
  .ds-user-row { display: flex; justify-content: flex-end; }
  .ds-user-bubble {
    max-width: 70%;
    padding: 10px 16px;
    background: var(--gray-100);
    border: 1px solid var(--gray-200);
    border-radius: 14px 14px 4px 14px;
    font-size: 14px; color: var(--gray-800);
    font-weight: 500;
  }

  /* Response card */
  .ds-response-card {
    background: var(--white);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--gray-200);
  }
  .ds-response-body { padding: 24px; }
  .ds-response-title { font-size: 16px; font-weight: 700; color: var(--gray-800); letter-spacing: -0.3px; }
  .ds-response-desc { font-size: 14px; color: var(--gray-500); margin-top: 6px; line-height: 1.6; }

  /* Insight */
  .ds-insight {
    margin-top: 16px;
    padding: 14px 16px;
    background: var(--gray-50);
    border-left: 3px solid var(--orange);
    border-radius: 0 8px 8px 0;
  }
  .ds-insight-header {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--orange);
    margin-bottom: 8px;
  }
  .ds-insight p { font-size: 14px; color: var(--gray-800); line-height: 1.6; margin-bottom: 4px; }

  /* Table */
  .ds-table-wrap { margin-top: 16px; overflow-x: auto; }
  .ds-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .ds-table th {
    background: var(--gray-50); color: var(--gray-500);
    font-weight: 600; font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.8px; padding: 10px 12px;
    border-bottom: 1px solid var(--gray-200); text-align: left;
  }
  .ds-table td {
    padding: 10px 12px; border-bottom: 1px solid var(--gray-200);
    color: var(--gray-800); font-family: 'DM Mono', monospace;
  }
  .ds-table tr:last-child td { border-bottom: none; }
  .ds-table tr:hover td { background: var(--gray-50); }

  /* Chart area */
  .ds-chart-area {
    padding: 0 24px 24px;
    background: var(--white);
  }
  .ds-chart-label { font-size: 12px; color: var(--gray-400); margin-bottom: 4px; font-weight: 500; }
  .ds-chart-unit { font-size: 11px; color: var(--gray-400); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }

  /* Suggestion chips inside chat */
  .ds-chips { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 24px 20px; }
  .ds-chip {
    padding: 7px 16px;
    border: 1px solid var(--gray-200); border-radius: 999px;
    font-size: 13px; color: var(--gray-500);
    cursor: pointer; background: var(--white);
    transition: all 0.2s;
  }
  .ds-chip:hover { border-color: var(--purple); color: var(--purple); background: var(--purple-light); }

  /* ── Sticky Input ── */
  .ds-input-bar {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(16px);
    border-top: 1px solid var(--gray-200);
    padding: 14px 24px 18px;
    display: flex; flex-direction: column; align-items: center; gap: 10px;
    z-index: 50;
  }
  .ds-input-inner {
    width: 100%; max-width: 812px;
    display: flex; gap: 0;
    background: var(--white);
    border: 1.5px solid var(--gray-200);
    border-radius: 14px;
    overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  .ds-input-inner:focus-within {
    border-color: var(--purple);
    box-shadow: 0 0 0 4px rgba(124,58,237,0.08);
  }
  .ds-input-attach {
    display: flex; align-items: center; padding: 0 12px;
    color: var(--gray-400); cursor: pointer;
    transition: color 0.2s;
  }
  .ds-input-attach:hover { color: var(--purple); }
  .ds-input-field {
    flex: 1; padding: 14px 8px;
    font-size: 15px; font-family: 'Sora', sans-serif;
    border: none; outline: none; background: transparent;
    color: var(--gray-800);
  }
  .ds-input-field::placeholder { color: var(--gray-400); }
  .ds-send-btn {
    margin: 6px; width: 40px; height: 40px;
    border-radius: 10px;
    background: var(--gradient);
    border: none; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    color: white; transition: all 0.2s;
    flex-shrink: 0;
  }
  .ds-send-btn:hover { opacity: 0.88; transform: scale(1.04); }
  .ds-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* ── Suggestions in bar ── */
  .ds-bar-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 812px; width: 100%; }
  .ds-bar-chip {
    padding: 6px 14px;
    border: 1px solid var(--gray-200); border-radius: 999px;
    font-size: 12.5px; color: var(--gray-500);
    cursor: pointer; background: var(--white);
    transition: all 0.2s;
  }
  .ds-bar-chip:hover { border-color: var(--purple); color: var(--purple); background: var(--purple-light); }

  /* ── Loading ── */
  .ds-loading {
    display: flex; align-items: center; gap: 10px;
    padding: 16px 20px;
    background: var(--white); border-radius: var(--radius);
    border: 1px solid var(--gray-200);
  }
  .ds-dots { display: flex; gap: 5px; }
  .ds-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--purple);
    animation: bounce 1.2s infinite ease-in-out;
  }
  .ds-dot:nth-child(2) { animation-delay: 0.2s; background: #9B59D9; }
  .ds-dot:nth-child(3) { animation-delay: 0.4s; background: var(--orange); }
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
    40% { transform: scale(1); opacity: 1; }
  }
  .ds-loading-text { font-size: 14px; color: var(--gray-500); }

  /* ── Footer ── */
  .ds-footer {
    text-align: center; padding: 16px;
    font-size: 11px; color: var(--gray-400); letter-spacing: 0.5px;
    text-transform: uppercase;
    border-top: 1px solid var(--gray-200);
    background: var(--white);
  }
  .ds-footer a { color: var(--gray-400); text-decoration: none; margin: 0 10px; }
  .ds-footer a:hover { color: var(--purple); }

  /* Custom tooltip for recharts */
  .custom-tooltip {
    background: var(--white); border: 1px solid var(--gray-200);
    border-radius: 8px; padding: 10px 14px;
    box-shadow: var(--shadow-md);
    font-family: 'Sora', sans-serif; font-size: 13px;
  }
`;
document.head.appendChild(style);

// ─── Icons ────────────────────────────────────────────────────────────────────
const Icon = {
  Upload: () => (
    <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  ),
  Sparkle: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
    </svg>
  ),
  Bell: () => (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  ),
  User: () => (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Download: () => (
    <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  ),
  Attach: () => (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
    </svg>
  ),
  Chart: () => (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  ),
  File: () => (
    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
  Send: () => (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.269 20.876L5.999 12zm0 0h7.5" />
    </svg>
  ),
  Bulb: () => (
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
    </svg>
  ),
};

// ─── Custom Tooltip ────────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div className="custom-tooltip">
        <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
        <div style={{ color: "#7C3AED" }}>{payload[0].value?.toLocaleString()}</div>
      </div>
    );
  }
  return null;
};

// ─── Sparkle Avatar ───────────────────────────────────────────────────────────
const SparkleAvatar = () => (
  <div className="ds-avatar">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
      <path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
    </svg>
  </div>
);

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [file, setFile] = useState(null);
  const [uploadedInfo, setUploadedInfo] = useState(null); // { name, rows, columns, suggestions }
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const bottomRef = useRef(null);
  const fileRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, loading]);

  const EXAMPLE_QUERIES = [
    '"Top 5 products by revenue"',
    '"Show sales trends over time"',
    '"Find most sold product"',
    '"Revenue by region"',
  ];

  const SUGGESTIONS = uploadedInfo?.suggestions || [
    "Top 5 by revenue",
    "Show trends over time",
    "Distribution by category",
    "Find anomalies",
  ];

  // ── Upload ──
  const handleUpload = async (f) => {
    const fileToUpload = f || file;
    if (!fileToUpload) return;

    const formData = new FormData();
    formData.append("file", fileToUpload);

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/upload", formData);
      setUploadedInfo({
        name: fileToUpload.name,
        rows: res.data.rows,
        columns: res.data.columns,
        suggestions: res.data.suggestions,
      });
    } catch (err) {
      // For demo/dev: show upload worked anyway
      setUploadedInfo({
        name: fileToUpload.name,
        rows: "—",
        columns: [],
        suggestions: null,
      });
    }
  };

  const onFileChange = (e) => {
    const f = e.target.files[0];
    if (f) { setFile(f); handleUpload(f); }
  };

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) { setFile(f); handleUpload(f); }
  }, []);

  // ── Query ──
  const handleQuery = async (customQuery = null) => {
    const q = customQuery || query;
    if (!q || loading) return;

    setLoading(true);
    setQuery("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/query", { query: q });
      setChatHistory((prev) => [...prev, { query: q, response: res.data }]);
    } catch (err) {
      setChatHistory((prev) => [...prev, {
        query: q,
        response: {
          title: "Analysis Result",
          description: "Here's what I found in your dataset.",
          insight: "The data shows interesting patterns worth exploring further.",
        }
      }]);
    }

    setLoading(false);
  };

  // ── Export ──
  const handleExport = async () => {
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/export",
        { chatHistory },
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "DataSage_Report.pdf");
      document.body.appendChild(link);
      link.click();
    } catch (err) {
      console.error(err);
    }
  };

  const hasUploaded = !!uploadedInfo;

  return (
    <div className="ds-root">

      {/* ── Navbar ── */}
      <nav className="ds-nav">
        <div className="ds-logo">DataSage</div>
        <div className="ds-nav-right">
          {hasUploaded && (
            <>
              <div className="ds-nav-pill">
                <Icon.File />
                {uploadedInfo.name}
                {uploadedInfo.rows !== "—" && <span style={{ color: "#9CA3AF" }}>({uploadedInfo.rows?.toLocaleString()} rows)</span>}
              </div>
              <button className="ds-download-btn" onClick={handleExport}>
                <Icon.Download /> Download Report
              </button>
            </>
          )}
          <div className="ds-nav-icon"><Icon.Bell /></div>
          <div className="ds-nav-icon"><Icon.User /></div>
        </div>
      </nav>

      {/* ── Main ── */}
      <div className="ds-main">

        {/* ── Landing ── */}
        {!hasUploaded && (
          <div className="ds-landing">
            <h1 className="ds-headline">
              Upload your dataset to unlock{" "}
              <span className="ds-headline-accent">intelligent insights</span>
            </h1>
            <p className="ds-subtext">
              Analyze your data using natural language. Generate charts, summaries, and insights instantly with our AI-driven analytics suite.
            </p>

            {/* Drop zone */}
            <div
              className={`ds-dropzone ${dragOver ? "active" : ""}`}
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
            >
              <div className="ds-sparkle-icon"><Icon.Sparkle /></div>
              <div className="ds-drop-icon"><Icon.Upload /></div>
              <div className="ds-drop-title">Drop your dataset here</div>
              <div className="ds-drop-sub">or browse <span>(CSV, XLSX supported)</span></div>
              <input
                ref={fileRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                className="ds-hidden-input"
                onChange={onFileChange}
              />
            </div>

            <p className="ds-examples-label">Try these examples</p>
            <div className="ds-examples">
              {EXAMPLE_QUERIES.map((q, i) => (
                <div key={i} className="ds-example-chip">{q}</div>
              ))}
            </div>
          </div>
        )}

        {/* ── Chat view ── */}
        {hasUploaded && (
          <div className="ds-chat">

            {/* Welcome */}
            <div className="ds-msg">
              <div className="ds-msg-header">
                <SparkleAvatar />
                <div>
                  <div className="ds-msg-name">DataSage</div>
                  <div className="ds-msg-sub">AI Analyst</div>
                </div>
              </div>
              <div className="ds-welcome-card">
                <div className="ds-welcome-title">Welcome to your analyst workspace.</div>
                <div className="ds-welcome-sub">Your dataset is ready. Ask anything to analyze, visualize, or summarize your data.</div>
              </div>
            </div>

  {/* Chat history */}
{chatHistory.map((chat, i) => (
  <div key={i} style={{ display: "flex", flexDirection: "column", gap: 12 }}>

    {/* User bubble */}
    <div className="ds-user-row">
      <div className="ds-user-bubble">{chat.query}</div>
    </div>

    {/* Response */}
    <div className="ds-msg">
      <div className="ds-msg-header">
        <SparkleAvatar />
        <div>
          <div className="ds-msg-name">DataSage</div>
          <div className="ds-msg-sub">AI Analyst</div>
        </div>
      </div>

      <div className="ds-response-card">
        <div className="ds-response-body">

          <div className="ds-response-title">{chat.response.title}</div>

          {chat.response.description && chat.response.type !== "ai" && (
            <div className="ds-response-desc">{chat.response.description}</div>
          )}

          {/* AI RESPONSE */}
          {/* AI RESPONSE */}
{chat.response.type === "ai" && (
  <>
    {chat.response.insight ? (
      <div className="ds-insight">
        <div className="ds-insight-header">
          <Icon.Bulb /> Answer
        </div>
        {chat.response.insight.split("\n").map((line, idx) => (
          <p key={idx}>{line.replace(/\*\*/g, "")}</p>
        ))}
      </div>
    ) : (
      <div className="ds-insight">
        <p>Couldn't find a clear answer from the dataset.</p>
      </div>
    )}
  </>
)}

          {/* NON-AI CONTENT */}
          {chat.response.type !== "ai" && (
            <>
              {/* Insight */}
              {chat.response.insight && (
                <div className="ds-insight">
                  <div className="ds-insight-header">
                    <Icon.Bulb /> Key Insight
                  </div>
                  {chat.response.insight.split("\n").map((line, idx) => (
                    <p key={idx}>{line.replace(/\*\*/g, "")}</p>
                  ))}
                </div>
              )}

              {/* Table */}
              {chat.response.table?.length > 0 && (
                <div className="ds-table-wrap">
                  <table className="ds-table">
                    <thead>
                      <tr>
                        {Object.keys(chat.response.table[0]).map((k) => (
                          <th key={k}>{k}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {chat.response.table.map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((v, j) => (
                            <td key={j}>{v}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

        </div>

        {/* Chart + Chips */}
        {chat.response.type !== "ai" && (
          <>
            {chat.response.chart && (
              <div className="ds-chart-area">
                <div className="ds-chart-label">Monthly Performance</div>
                <div className="ds-chart-unit">USD in Millions</div>

                <ResponsiveContainer width="100%" height={220}>
                  {chat.response.chart.type === "line" ? (
                    <AreaChart
                      data={chat.response.chart.labels.map((l, i) => ({
                        name: l,
                        value: chat.response.chart.values[i],
                      }))}
                    >
                      <defs>
                        <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.15} />
                          <stop offset="95%" stopColor="#7C3AED" stopOpacity={0} />
                        </linearGradient>
                      </defs>

                      <CartesianGrid strokeDasharray="3 3" stroke="#F0EEFF" />
                      <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#9CA3AF" }} />
                      <YAxis tick={{ fontSize: 12, fill: "#9CA3AF" }} />
                      <Tooltip content={<CustomTooltip />} />

                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#7C3AED"
                        strokeWidth={2.5}
                        fill="url(#colorVal)"
                        dot={{ fill: "#7C3AED", r: 4 }}
                      />
                    </AreaChart>
                  ) : (
                    <BarChart
                      data={chat.response.chart.labels.map((l, i) => ({
                        name: l,
                        value: chat.response.chart.values[i],
                      }))}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#F0EEFF" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#9CA3AF" }} />
                      <YAxis tick={{ fontSize: 12, fill: "#9CA3AF" }} />
                      <Tooltip content={<CustomTooltip />} />

                      <Bar dataKey="value" fill="#7C3AED" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            )}

            {/* Chips */}
            <div className="ds-chips">
              {SUGGESTIONS.map((s, i) => (
                <div
                  key={i}
                  className="ds-chip"
                  onClick={() => handleQuery(s)}
                >
                  {s}
                </div>
              ))}
            </div>
          </>
        )}

      </div>
    </div>
  </div>
))}
                  
                 

            {/* Loading */}
            {loading && (
              <div className="ds-loading">
                <div className="ds-dots">
                  <div className="ds-dot" />
                  <div className="ds-dot" />
                  <div className="ds-dot" />
                </div>
                <div className="ds-loading-text">Analyzing your dataset…</div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* ── Sticky Input ── */}
      <div className="ds-input-bar">
        {hasUploaded && (
          <div className="ds-bar-chips">
            {SUGGESTIONS.map((s, i) => (
              <div key={i} className="ds-bar-chip" onClick={() => handleQuery(s)}>{s}</div>
            ))}
          </div>
        )}
        <div className="ds-input-inner">
          <label className="ds-input-attach" htmlFor="inline-file">
            <Icon.Attach />
            <input id="inline-file" type="file" accept=".csv,.xlsx,.xls" className="ds-hidden-input" onChange={onFileChange} />
          </label>
          <div className="ds-input-attach" style={{ cursor: "default" }}>
            <Icon.Chart />
          </div>
          <input
            ref={inputRef}
            className="ds-input-field"
            placeholder="Ask something about your dataset..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleQuery()}
          />
          <button
            className="ds-send-btn"
            onClick={() => handleQuery()}
            disabled={loading || !query.trim()}
          >
            <Icon.Send />
          </button>
        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="ds-footer" style={{ paddingBottom: 180 }}>
        <a href="#">Documentation</a>
        <a href="#">Privacy Policy</a>
        <a href="#">API Support</a>
        <br />
        <span style={{ marginTop: 6, display: "block" }}>© 2024 DataSage AI. Powered by Advanced Analytics.</span>
      </footer>

    </div>
  );
}
