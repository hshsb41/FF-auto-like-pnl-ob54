import os
import time
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template_string, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ckrpro_secure_session_key_99281')

DATA_STORE = {
    "licenses": {
        "ADMIN-SECRET-SAMU": {
            "key": "ADMIN-SECRET-SAMU",
            "type": "admin",
            "duration": "Unlimited",
            "expires": None,
            "auto_uid": None,
            "auto_expires": None,
            "auto_days": "Unlimited",
            "last_used_date": None,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }
    },
    "history": [],
    "stats": {
        "total_requests": 0
    },
    "admin_password": "ADMIN-SECRET-SAMU"
}

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>CKRPRO - Professional Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        bgdark: '#0F1117',
                        carddark: '#171B22',
                        inputdark: '#20252D',
                        primary: '#2D7DFF',
                        accent: '#5EA3FF',
                        success: '#22C55E',
                        danger: '#EF4444',
                        warning: '#F59E0B',
                        txtwhite: '#FFFFFF',
                        txtgray: '#9CA3AF'
                    },
                    fontFamily: {
                        sans: ['Inter', 'sans-serif']
                    }
                }
            }
        }
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0F1117; color: #FFFFFF; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #0F1117; }
        ::-webkit-scrollbar-thumb { background: #20252D; border-radius: 9999px; }
        * { border: none !important; outline: none !important; box-shadow: none; }
        .soft-shadow { box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25); }
    </style>
</head>
<body class="bg-bgdark text-txtwhite font-sans text-xs antialiased">

    <div id="toast-container" class="fixed top-4 right-4 z-50 flex flex-col space-y-2 pointer-events-none"></div>

    <a href="https://wa.me/9840825493?text=Help%20me%20sir" target="_blank" class="fixed bottom-5 right-5 z-40 w-11 h-11 bg-success text-white rounded-full flex items-center justify-center soft-shadow hover:scale-105 transition-all">
        <i class="fa-brands fa-whatsapp text-lg"></i>
    </a>

    <div id="admin-auth-modal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 hidden">
        <div class="w-full max-w-xs bg-carddark rounded-2xl p-5 soft-shadow space-y-4">
            <div>
                <h3 class="font-bold text-white uppercase tracking-wider text-xs flex items-center space-x-2">
                    <i class="fa-solid fa-lock text-primary"></i>
                    <span> </span>
                </h3>
                <p class="text-[10px] text-txtgray font-bold mt-1">ADMIN KEY</p>
            </div>
            <div class="relative">
                <input type="password" id="admin-pass-input" placeholder="Password" class="w-full bg-inputdark text-xs rounded-xl py-2.5 pl-3 pr-9 text-white font-bold placeholder-txtgray/40">
                <button type="button" onclick="toggleAdminPassVisibility()" class="absolute right-3 top-2.5 text-txtgray hover:text-white">
                    <i id="admin-eye-icon" class="fa-solid fa-eye text-xs"></i>
                </button>
            </div>
            <div class="flex space-x-2">
                <button onclick="closeAdminAuth()" class="flex-1 bg-inputdark hover:bg-inputdark/80 text-txtgray hover:text-white text-xs font-bold py-2.5 rounded-xl transition-all">Cancel</button>
                <button onclick="verifyAdminPassword()" class="flex-1 bg-primary hover:bg-primary/90 text-white text-xs font-bold py-2.5 rounded-xl transition-all">Unlock</button>
            </div>
        </div>
    </div>

    <div id="login-view" class="min-h-screen flex items-center justify-center p-4">
        <div class="w-full max-w-xs bg-carddark rounded-2xl p-6 soft-shadow transition-all duration-300">
            <div class="mb-5">
                <h1 class="text-xs font-bold tracking-tight uppercase text-white"> </h1>
                <p class="text-[10px] text-txtgray font-bold mt-0.5">ENTER LICENSE KEY</p>
            </div>
            <form id="login-form" onsubmit="handleLogin(event)" class="space-y-3">
                <div>
                    <input type="text" id="license-key-input" required placeholder="License Key" class="w-full bg-inputdark text-xs rounded-xl py-2.5 px-3 text-white placeholder-txtgray/40 font-bold">
                </div>
                <button type="submit" id="login-btn" class="w-full bg-primary hover:bg-primary/90 text-white text-xs font-bold py-2.5 rounded-xl transition-all flex items-center justify-center space-x-2">
                    <span>LOGIN</span>
                </button>
            </form>
        </div>
    </div>

    <div id="app-view" class="min-h-screen flex hidden">
        <aside class="w-56 bg-carddark flex flex-col fixed inset-y-0 left-0 z-30 transition-transform duration-300 -translate-x-full lg:translate-x-0 soft-shadow" id="sidebar">
            <div class="h-12 flex items-center px-5 space-x-2">
                <span class="font-bold tracking-wide text-xs text-white uppercase"> </span>
            </div>
            <nav class="flex-1 px-3 py-3 space-y-1 font-bold">
                <a href="#dashboard" onclick="switchTab('dashboard')" class="nav-item flex items-center space-x-3 px-3 py-2 rounded-xl text-txtgray hover:text-white hover:bg-inputdark transition-all active" data-tab="dashboard">
                    <i class="fa-solid fa-chart-pie w-4 text-center"></i>
                    <span>Dashboard</span>
                </a>
                <a href="#send-likes" onclick="switchTab('send-likes')" class="nav-item flex items-center space-x-3 px-3 py-2 rounded-xl text-txtgray hover:text-white hover:bg-inputdark transition-all" data-tab="send-likes">
                    <i class="fa-solid fa-paper-plane w-4 text-center"></i>
                    <span>Send Likes</span>
                </a>
                <a href="#auto-likes" onclick="switchTab('auto-likes')" class="nav-item flex items-center space-x-3 px-3 py-2 rounded-xl text-txtgray hover:text-white hover:bg-inputdark transition-all" data-tab="auto-likes">
                    <i class="fa-solid fa-robot w-4 text-center"></i>
                    <span>Auto Like Setup</span>
                </a>
                <a href="#price-list" onclick="switchTab('price-list')" class="nav-item flex items-center space-x-3 px-3 py-2 rounded-xl text-txtgray hover:text-white hover:bg-inputdark transition-all" data-tab="price-list">
                    <i class="fa-solid fa-gem w-4 text-center"></i>
                    <span>Price List</span>
                </a>
                <a href="#generator" onclick="requestKeyGeneratorAccess()" class="nav-item flex items-center space-x-3 px-3 py-2 rounded-xl text-txtgray hover:text-white hover:bg-inputdark transition-all" data-tab="generator">
                    <i class="fa-solid fa-key w-4 text-center"></i>
                    <span>Key Generator</span>
                </a>
                <a href="#history" onclick="switchTab('history')" class="nav-item flex items-center space-x-3 px-3 py-2 rounded-xl text-txtgray hover:text-white hover:bg-inputdark transition-all" data-tab="history">
                    <i class="fa-solid fa-history w-4 text-center"></i>
                    <span>History</span>
                </a>
                <a href="#support" onclick="switchTab('support')" class="nav-item flex items-center space-x-3 px-3 py-2 rounded-xl text-txtgray hover:text-white hover:bg-inputdark transition-all" data-tab="support">
                    <i class="fa-brands fa-whatsapp w-4 text-center"></i>
                    <span>Support</span>
                </a>
            </nav>
            <div class="p-3">
                <button onclick="logout()" class="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-danger hover:bg-danger/10 transition-all font-bold">
                    <i class="fa-solid fa-arrow-right-from-bracket w-4 text-center"></i>
                    <span>Logout</span>
                </button>
            </div>
        </aside>

        <div class="flex-1 flex flex-col lg:pl-56 w-full">
            <header class="h-12 bg-carddark flex items-center justify-between px-4 lg:hidden sticky top-0 z-20">
                <button onclick="toggleSidebar()" class="text-txtgray hover:text-white">
                    <i class="fa-solid fa-bars text-sm"></i>
                </button>
                <span class="text-xs font-bold uppercase"> </span>
            </header>

            <main class="flex-1 p-3 sm:p-5 max-w-4xl w-full mx-auto space-y-4">
                
                <div id="tab-dashboard" class="tab-content space-y-3">
                    <div id="dashboard-stats-grid" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div class="bg-carddark p-3.5 rounded-2xl flex items-center justify-between soft-shadow">
                            <div>
                                <p class="text-[9px] font-bold text-txtgray uppercase tracking-wider">License Type</p>
                                <h3 id="stat-license-type" class="text-xs font-bold mt-0.5 text-white">--</h3>
                            </div>
                            <div class="w-7 h-7 rounded-xl bg-success/10 text-success flex items-center justify-center text-xs">
                                <i class="fa-solid fa-shield"></i>
                            </div>
                        </div>
                        <div class="bg-carddark p-3.5 rounded-2xl flex items-center justify-between soft-shadow">
                            <div>
                                <p class="text-[9px] font-bold text-txtgray uppercase tracking-wider">Remaining Duration</p>
                                <h3 id="stat-remaining-days" class="text-xs font-bold mt-0.5 text-white">--</h3>
                            </div>
                            <div class="w-7 h-7 rounded-xl bg-accent/10 text-accent flex items-center justify-center text-xs">
                                <i class="fa-solid fa-clock"></i>
                            </div>
                        </div>
                        <div class="bg-carddark p-3.5 rounded-2xl flex items-center justify-between soft-shadow">
                            <div>
                                <p class="text-[9px] font-bold text-txtgray uppercase tracking-wider">Auto-Like Status</p>
                                <h3 id="stat-auto-status" class="text-xs font-bold mt-0.5 text-success">Not Set</h3>
                            </div>
                            <div class="w-7 h-7 rounded-xl bg-success/10 text-success flex items-center justify-center text-xs">
                                <i class="fa-solid fa-robot"></i>
                            </div>
                        </div>
                        <div class="bg-carddark p-3.5 rounded-2xl flex items-center justify-between soft-shadow">
                            <div>
                                <p class="text-[9px] font-bold text-txtgray uppercase tracking-wider">Total Requests</p>
                                <h3 id="stat-total-req" class="text-xs font-bold mt-0.5 text-white">0</h3>
                            </div>
                            <div class="w-7 h-7 rounded-xl bg-primary/10 text-primary flex items-center justify-center text-xs">
                                <i class="fa-solid fa-paper-plane"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="tab-send-likes" class="tab-content hidden space-y-3">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        <div class="bg-carddark rounded-2xl p-4 space-y-3 soft-shadow">
                            <h2 class="text-xs font-bold uppercase tracking-wider text-txtgray">SEND LIKE</h2>
                            <form id="send-likes-form" onsubmit="handleSendLikes(event)" class="space-y-2.5">
                                <div>
                                    <label class="block text-[9px] font-bold text-txtgray mb-1 uppercase tracking-wider">UID</label>
                                    <input type="number" id="uid-input" required placeholder="Enter UID" class="w-full bg-inputdark text-xs rounded-xl py-2 px-3 text-white placeholder-txtgray/40 font-bold">
                                    <p class="text-[9px] text-txtgray mt-1"> </p>
                                </div>
                                <button type="submit" id="send-btn" class="w-full bg-primary hover:bg-primary/90 text-white text-xs font-bold py-2.5 rounded-xl transition-all flex items-center justify-center space-x-2">
                                    <span id="send-btn-text">SEND NORMAL LIKES</span>
                                </button>
                            </form>
                        </div>

                        <div class="bg-carddark rounded-2xl p-4 flex flex-col justify-center items-center text-center min-h-[220px] soft-shadow">
                            <div id="result-placeholder" class="py-6 space-y-2">
                                <div class="w-9 h-9 rounded-xl bg-inputdark flex items-center justify-center text-txtgray mx-auto text-xs">
                                    <i class="fa-solid fa-fire"></i>
                                </div>
                                <p class="text-xs font-bold text-txtgray">No active response</p>
                            </div>

                            <div id="result-loading" class="hidden py-6 space-y-2.5">
                                <div class="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto"></div>
                                <p class="text-xs font-bold text-txtgray">Processing request...</p>
                            </div>

                            <div id="result-card" class="hidden w-full text-left space-y-2.5 text-xs">
                                <div class="flex items-center justify-between pb-2.5">
                                    <div>
                                        <h4 class="font-bold text-white" id="res-nickname">--</h4>
                                        <p class="text-[9px] font-bold text-txtgray">UID: <span id="res-uid">--</span></p>
                                    </div>
                                    <span class="px-2 py-0.5 bg-success/10 text-success text-[9px] font-bold rounded uppercase tracking-wider">Success</span>
                                </div>
                                <div class="grid grid-cols-3 gap-2 text-center">
                                    <div class="bg-inputdark p-2 rounded-xl">
                                        <p class="text-[8px] text-txtgray uppercase font-bold">Before</p>
                                        <p class="font-bold mt-0.5 text-white" id="res-before">--</p>
                                    </div>
                                    <div class="bg-inputdark p-2 rounded-xl">
                                        <p class="text-[8px] text-txtgray uppercase font-bold">Given</p>
                                        <p class="font-bold text-primary mt-0.5" id="res-given">--</p>
                                    </div>
                                    <div class="bg-inputdark p-2 rounded-xl">
                                        <p class="text-[8px] text-txtgray uppercase font-bold">After</p>
                                        <p class="font-bold text-success mt-0.5" id="res-after">--</p>
                                    </div>
                                </div>
                                <div class="bg-inputdark p-2 rounded-xl text-[10px] text-txtgray font-bold">
                                    <span class="text-white">Note:</span> <span id="res-note">--</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="tab-auto-likes" class="tab-content hidden space-y-3">
                    <div class="max-w-md mx-auto bg-carddark rounded-2xl p-5 space-y-4 soft-shadow">
                        <div>
                            <h2 class="text-xs font-bold uppercase tracking-wider text-white flex items-center space-x-2">
                                <i class="fa-solid fa-robot text-success"></i>
                                <span id="auto-setup-title">Auto Like Daily Setup</span>
                            </h2>
                            <p id="auto-setup-desc" class="text-[10px] text-txtgray font-bold mt-1">Enter Target UID, select duration days, and setup automatic daily likes at 8:30 AM Nepal Time.</p>
                        </div>
                        <form id="auto-like-form" onsubmit="handleSaveAutoLike(event)" class="space-y-3">
                            <div>
                                <label class="block text-[9px] font-bold text-txtgray mb-1 uppercase tracking-wider">Auto-Like Target UID</label>
                                <input type="number" id="auto-uid-input" required placeholder="Enter UID for Auto Likes" class="w-full bg-inputdark text-xs rounded-xl py-2.5 px-3 text-white placeholder-txtgray/40 font-bold">
                            </div>
                            <div>
                                <label class="block text-[9px] font-bold text-txtgray mb-1 uppercase tracking-wider">Auto-Like Duration (Days)</label>
                                <input type="number" id="auto-days-input" min="1" max="365" value="30" required placeholder="Duration in Days" class="w-full bg-inputdark text-xs rounded-xl py-2.5 px-3 text-white placeholder-txtgray/40 font-bold">
                                <p class="text-[8px] text-txtgray mt-1"> </p>
                            </div>
                            <div id="admin-key-field-container">
                                <label class="block text-[9px] font-bold text-txtgray mb-1 uppercase tracking-wider">Admin Key Authentication</label>
                                <input type="password" id="auto-admin-key-input" placeholder="Enter Admin Key" class="w-full bg-inputdark text-xs rounded-xl py-2.5 px-3 text-white placeholder-txtgray/40 font-bold">
                            </div>
                            <div class="bg-inputdark p-3 rounded-xl space-y-1">
                                <p class="text-[9px] text-txtgray font-bold">Current Auto Status:</p>
                                <p id="current-auto-uid-display" class="text-xs font-mono font-bold text-accent">Not Registered</p>
                            </div>
                            <button type="submit" id="auto-save-btn" class="w-full bg-success hover:bg-success/90 text-white text-xs font-bold py-2.5 rounded-xl transition-all">
                                SAVE AUTO-LIKE CONFIG
                            </button>
                        </form>
                    </div>
                </div>

                <div id="tab-price-list" class="tab-content hidden space-y-3">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
                        <div class="bg-carddark p-4 rounded-2xl flex flex-col justify-between space-y-3 soft-shadow">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-white uppercase tracking-wider">15 Days Plan</span>
                                <i class="fa-solid fa-gem text-accent"></i>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-txtgray font-bold">PRICE</span>
                                <span class="font-bold text-success text-sm">Rs. 400</span>
                            </div>
                            <a href="https://wa.me/9840825493?text=Hello,%20I%20want%20to%20buy%20a%2015%20Day%20license." target="_blank" class="w-full bg-primary hover:bg-primary/90 text-white font-bold text-center py-2.5 rounded-xl text-xs transition-all flex items-center justify-center space-x-1.5">
                                <span>BUY</span>
                            </a>
                        </div>
                        <div class="bg-carddark p-4 rounded-2xl flex flex-col justify-between space-y-3 soft-shadow">
                            <div class="flex items-center justify-between">
                                <span class="font-bold text-white uppercase tracking-wider">30 Days Plan</span>
                                <i class="fa-solid fa-fire text-danger"></i>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-txtgray font-bold">PRICE</span>
                                <span class="font-bold text-success text-sm">Rs. 800</span>
                            </div>
                            <a href="https://wa.me/9840825493?text=Hello,%20I%20want%20to%20buy%20a%2030%20Day%20license." target="_blank" class="w-full bg-primary hover:bg-primary/90 text-white font-bold text-center py-2.5 rounded-xl text-xs transition-all flex items-center justify-center space-x-1.5">
                                <span>BUY</span>
                            </a>
                        </div>
                    </div>
                </div>

                <div id="tab-generator" class="tab-content hidden space-y-3">
                    <div class="bg-carddark rounded-2xl p-4 space-y-3 soft-shadow">
                        <div class="flex flex-col sm:flex-row items-center justify-between gap-2">
                            <h2 class="text-xs font-bold uppercase tracking-wider text-txtgray">Key Generator</h2>
                            <div class="flex items-center space-x-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
                                <input type="text" id="gen-search" oninput="filterKeys()" placeholder="Search keys..." class="bg-inputdark text-xs rounded-xl py-1.5 px-2.5 text-white w-full sm:w-36 font-bold placeholder-txtgray/40">
                                <button onclick="refreshKeys()" class="bg-inputdark hover:bg-inputdark/80 text-white text-xs font-bold px-2.5 py-1.5 rounded-xl transition-all" title="Refresh List">
                                    <i class="fa-solid fa-rotate"></i>
                                </button>
                                <button onclick="deleteExpiredKeys()" class="bg-warning/10 text-warning hover:bg-warning/20 text-xs font-bold px-2.5 py-1.5 rounded-xl transition-all whitespace-nowrap" title="Delete Expired">
                                    <i class="fa-solid fa-clock-rotate-left"></i> Delete Expired
                                </button>
                                <button onclick="clearAllKeys()" class="bg-danger/10 text-danger hover:bg-danger/20 text-xs font-bold px-2.5 py-1.5 rounded-xl transition-all" title="Clear All">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <form onsubmit="handleGenerateKey(event)" class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                            <input type="text" id="gen-username" placeholder="Username (optional)" class="bg-inputdark text-xs rounded-xl py-2 px-3 text-white font-bold placeholder-txtgray/40">
                            <input type="number" id="gen-duration" min="1" max="3650" value="30" required placeholder="Duration (Days)" class="bg-inputdark text-xs rounded-xl py-2 px-3 text-white font-bold placeholder-txtgray/40">
                            <button type="submit" class="bg-primary hover:bg-primary/90 text-white text-xs font-bold py-2 rounded-xl transition-all">
                                GENERATR KEY
                            </button>
                        </form>
                        <div class="overflow-x-auto pt-1">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-inputdark text-txtgray uppercase text-[8px] font-bold">
                                    <tr>
                                        <th class="p-2 rounded-l-xl">License Key</th>
                                        <th class="p-2">Duration</th>
                                        <th class="p-2">Created</th>
                                        <th class="p-2">Expiry</th>
                                        <th class="p-2">Status</th>
                                        <th class="p-2 rounded-r-xl text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="keys-table-body" class="font-bold">
                                    <tr><td colspan="6" class="text-center py-4 text-txtgray">No keys generated.</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div id="tab-history" class="tab-content hidden space-y-3">
                    <div class="bg-carddark rounded-2xl p-4 space-y-3 soft-shadow">
                        <div class="flex flex-col sm:flex-row items-center justify-between gap-2">
                            <input type="text" id="history-search" oninput="filterHistory()" placeholder="Search UID or Nickname..." class="bg-inputdark text-xs rounded-xl py-1.5 px-2.5 text-white w-full max-w-xs font-bold placeholder-txtgray/40">
                            <div class="flex items-center space-x-2 w-full sm:w-auto justify-between sm:justify-end">
                                <span id="history-total-likes" class="text-[10px] font-bold text-accent">TOTAL LIKES : 0</span>
                                <button onclick="clearHistory()" class="bg-danger/10 text-danger hover:bg-danger/20 text-xs font-bold px-3 py-1.5 rounded-xl transition-all">Clear</button>
                            </div>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-inputdark text-txtgray uppercase text-[8px] font-bold">
                                    <tr>
                                        <th class="p-2 rounded-l-xl">UID</th>
                                        <th class="p-2">Nickname</th>
                                        <th class="p-2">Likes Given</th>
                                        <th class="p-2">Date & Time</th>
                                        <th class="p-2 rounded-r-xl">Status</th>
                                    </tr>
                                </thead>
                                <tbody id="history-table-body" class="font-bold">
                                    <tr><td colspan="5" class="text-center py-4 text-txtgray">No records found.</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div id="tab-support" class="tab-content hidden space-y-3">
                    <div class="bg-carddark rounded-2xl p-5 max-w-xs text-center space-y-2.5 mx-auto soft-shadow">
                        <div class="w-10 h-10 rounded-xl bg-success/10 text-success flex items-center justify-center mx-auto text-sm">
                            <i class="fa-brands fa-whatsapp"></i>
                        </div>
                        <h2 class="text-xs font-bold text-white uppercase tracking-wider">Customer Support</h2>
                        <p class="text-[10px] text-txtgray font-bold">THANK YOU FOR CHOOSING CKRPRO. IF YOU EXPERIENCE ANY ISSUES WITH YOUR LICENSE, ACCOUNT, LOGIN, OR ANY OTHER SERVICE, PLEASE CONTACT OUR SUPPORT TEAM.</p>
                        <a href="https://wa.me/9840825493?text=Help%20me%20sir" target="_blank" class="inline-block bg-success hover:bg-success/90 text-white font-bold text-xs py-2 px-4 rounded-xl transition-all">
                            CHAT ON WHATSAPP
                        </a>
                    </div>
                </div>

            </main>
        </div>
    </div>

    <script>
        let currentKey = '';
        let currentUserData = null;
        let adminAuthenticated = false;

        function showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `pointer-events-auto px-3 py-2 rounded-xl soft-shadow text-xs font-bold ${type === 'error' ? 'bg-danger text-white' : 'bg-success text-white'}`;
            toast.innerText = message;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 2500);
        }

        window.addEventListener('load', () => {
            const savedKey = sessionStorage.getItem('ckrpro_key');
            if (savedKey) verifyKey(savedKey, true);
        });

        async function handleLogin(e) {
            e.preventDefault();
            const key = document.getElementById('license-key-input').value.trim();
            await verifyKey(key, false);
        }

        async function verifyKey(key, silent = false) {
            try {
                const res = await fetch('/api/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key })
                });
                const data = await res.json();
                if (data.status === 1) {
                    currentKey = key;
                    currentUserData = data;
                    sessionStorage.setItem('ckrpro_key', key);
                    document.getElementById('login-view').classList.add('hidden');
                    document.getElementById('app-view').classList.remove('hidden');
                    updateDashboard(data);
                    if (!silent) showToast('Logged in successfully');
                } else {
                    sessionStorage.removeItem('ckrpro_key');
                    if (!silent) showToast(data.message || 'Invalid key', 'error');
                }
            } catch (err) {
                if (!silent) showToast('Network error', 'error');
            }
        }

        function updateDashboard(data) {
            document.getElementById('stat-license-type').innerText = data.is_admin ? 'Admin' : 'Customer';
            document.getElementById('stat-remaining-days').innerText = data.remaining_days;
            document.getElementById('stat-total-req').innerText = data.stats.total_requests;

            const autoUidDisplay = document.getElementById('current-auto-uid-display');
            const statAutoStatus = document.getElementById('stat-auto-status');
            if (data.auto_uid) {
                autoUidDisplay.innerHTML = `UID: ${data.auto_uid} | Expires: ${data.auto_expires_str || 'Unlimited'}`;
                statAutoStatus.innerText = 'Active';
                statAutoStatus.className = 'text-xs font-bold mt-0.5 text-success';
                document.getElementById('auto-uid-input').value = data.auto_uid;
                if (data.auto_days_val) {
                    document.getElementById('auto-days-input').value = data.auto_days_val;
                }
            } else {
                autoUidDisplay.innerText = 'Not Registered';
                statAutoStatus.innerText = 'Not Set';
                statAutoStatus.className = 'text-xs font-bold mt-0.5 text-warning';
            }

            const adminKeyField = document.getElementById('admin-key-field-container');
            const autoSetupTitle = document.getElementById('auto-setup-title');
            const autoSetupDesc = document.getElementById('auto-setup-desc');

            if (data.is_admin) {
                adminKeyField.classList.add('hidden');
                document.getElementById('auto-admin-key-input').required = false;
                autoSetupTitle.innerText = 'AUTO LIKE';
                autoSetupDesc.innerText = 'Admin auto-like target UID runs daily at 8:30 AM';
            } else {
                adminKeyField.classList.remove('hidden');
                document.getElementById('auto-admin-key-input').required = true;
                autoSetupTitle.innerText = 'AUTO LIKE';
                autoSetupDesc.innerText = 'Enter Target UID, select duration days, and setup automatic daily likes at 8:30 AM';
            }

            const statsGrid = document.getElementById('dashboard-stats-grid');
            if (data.is_admin) {
                if (!document.getElementById('stat-active-keys-card')) {
                    const card = document.createElement('div');
                    card.id = 'stat-active-keys-card';
                    card.className = 'bg-carddark p-3.5 rounded-2xl flex items-center justify-between soft-shadow';
                    card.innerHTML = `
                        <div>
                            <p class="text-[9px] font-bold text-txtgray uppercase tracking-wider">Active Keys</p>
                            <h3 id="stat-active-keys" class="text-xs font-bold mt-0.5 text-white">0</h3>
                        </div>
                        <div class="w-7 h-7 rounded-xl bg-warning/10 text-warning flex items-center justify-center text-xs">
                            <i class="fa-solid fa-key"></i>
                        </div>
                    `;
                    statsGrid.appendChild(card);
                }
                document.getElementById('stat-active-keys').innerText = data.keys_list ? data.keys_list.length : 0;
                renderKeysTable(data.keys_list);
            } else {
                const card = document.getElementById('stat-active-keys-card');
                if (card) card.remove();
            }

            renderHistory(data.history);
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.getElementById(`tab-${tabId}`).classList.remove('hidden');
            document.querySelectorAll('.nav-item').forEach(el => {
                el.classList.remove('bg-inputdark', 'text-white');
                if (el.getAttribute('data-tab') === tabId) el.classList.add('bg-inputdark', 'text-white');
            });
            if (window.innerWidth < 1024) document.getElementById('sidebar').classList.add('-translate-x-full');
        }

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('-translate-x-full');
        }

        function requestKeyGeneratorAccess() {
            if (currentUserData && currentUserData.is_admin) {
                if (adminAuthenticated) {
                    switchTab('generator');
                } else {
                    document.getElementById('admin-pass-input').value = '';
                    document.getElementById('admin-auth-modal').classList.remove('hidden');
                }
            } else {
                showToast('Access denied: Admin only', 'error');
            }
        }

        function toggleAdminPassVisibility() {
            const input = document.getElementById('admin-pass-input');
            const icon = document.getElementById('admin-eye-icon');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }

        function closeAdminAuth() {
            document.getElementById('admin-auth-modal').classList.add('hidden');
        }

        async function verifyAdminPassword() {
            const pass = document.getElementById('admin-pass-input').value.trim();
            try {
                const res = await fetch('/api/verify-admin-pass', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: currentKey, password: pass })
                });
                const data = await res.json();
                if (data.status === 1) {
                    adminAuthenticated = true;
                    closeAdminAuth();
                    switchTab('generator');
                    showToast('Admin authenticated');
                } else {
                    showToast('Incorrect Admin Password', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }

        async function handleSendLikes(e) {
            e.preventDefault();
            const uid = document.getElementById('uid-input').value.trim();
            if (!uid) return;

            document.getElementById('result-placeholder').classList.add('hidden');
            document.getElementById('result-card').classList.add('hidden');
            document.getElementById('result-loading').classList.remove('hidden');
            const btn = document.getElementById('send-btn');
            const btnText = document.getElementById('send-btn-text');
            btn.disabled = true;
            btnText.innerText = 'Processing...';

            try {
                const res = await fetch('/api/send-likes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: currentKey, uid })
                });
                const data = await res.json();
                document.getElementById('result-loading').classList.add('hidden');
                btn.disabled = false;
                btnText.innerText = 'SEND NORMAL LIKES';

                if (data.status === 1) {
                    document.getElementById('res-nickname').innerText = data.PlayerNickname;
                    document.getElementById('res-uid').innerText = data.UID;
                    document.getElementById('res-before').innerText = data.LikesbeforeCommand;
                    document.getElementById('res-given').innerText = data.LikesGivenByAPI;
                    document.getElementById('res-after').innerText = data.LikesafterCommand;
                    document.getElementById('res-note').innerText = data.Note;
                    document.getElementById('result-card').classList.remove('hidden');
                    showToast('Normal likes sent successfully');
                    verifyKey(currentKey, true);
                } else {
                    document.getElementById('result-placeholder').classList.remove('hidden');
                    showToast(data.message || 'Request failed', 'error');
                }
            } catch (err) {
                document.getElementById('result-loading').classList.add('hidden');
                document.getElementById('result-placeholder').classList.remove('hidden');
                btn.disabled = false;
                btnText.innerText = 'SEND NORMAL LIKES';
                showToast('Network error', 'error');
            }
        }

        async function handleSaveAutoLike(e) {
            e.preventDefault();
            const uid = document.getElementById('auto-uid-input').value.trim();
            const days = document.getElementById('auto-days-input').value.trim();
            const adminKey = currentUserData && currentUserData.is_admin ? currentKey : document.getElementById('auto-admin-key-input').value.trim();
            if (!uid) return;

            try {
                const res = await fetch('/api/save-auto-uid', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: currentKey, uid, days, admin_key: adminKey })
                });
                const data = await res.json();
                if (data.status === 1) {
                    showToast('Auto-Like configured successfully');
                    if (!currentUserData.is_admin) {
                        document.getElementById('auto-admin-key-input').value = '';
                    }
                    verifyKey(currentKey, true);
                } else {
                    showToast(data.message || 'Failed to configure auto-like', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }

        async function handleGenerateKey(e) {
            e.preventDefault();
            const username = document.getElementById('gen-username').value.trim();
            const duration = document.getElementById('gen-duration').value;

            try {
                const res = await fetch('/api/generate-key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: currentKey, username, duration })
                });
                const data = await res.json();
                if (data.status === 1) {
                    showToast('Key generated successfully');
                    document.getElementById('gen-username').value = '';
                    verifyKey(currentKey, true);
                } else {
                    showToast(data.message || 'Failed to GENERATR KEY', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }

        async function deleteKey(targetKey) {
            try {
                const res = await fetch('/api/delete-key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: currentKey, target_key: targetKey })
                });
                const data = await res.json();
                if (data.status === 1) {
                    showToast('Key deleted');
                    verifyKey(currentKey, true);
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }

        async function deleteExpiredKeys() {
            try {
                const res = await fetch('/api/delete-expired-keys', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: currentKey })
                });
                const data = await res.json();
                if (data.status === 1) {
                    showToast('Expired keys removed');
                    verifyKey(currentKey, true);
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }

        function copyKey(targetKey) {
            navigator.clipboard.writeText(targetKey);
            showToast('Copied to clipboard');
        }

        function renderKeysTable(list) {
            const tbody = document.getElementById('keys-table-body');
            if (!list || list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-txtgray">No keys generated.</td></tr>`;
                return;
            }
            tbody.innerHTML = list.map(item => `
                <tr class="hover:bg-inputdark/30">
                    <td class="p-2 font-mono text-white">${item.key}</td>
                    <td class="p-2">${item.duration}</td>
                    <td class="p-2 text-txtgray">${item.created_at}</td>
                    <td class="p-2 text-txtgray">${item.expires_str}</td>
                    <td class="p-2"><span class="px-2 py-0.5 bg-success/10 text-success rounded text-[8px] font-bold uppercase">Active</span></td>
                    <td class="p-2 text-right space-x-1">
                        <button onclick="copyKey('${item.key}')" class="text-primary hover:underline px-1" title="Copy"><i class="fa-solid fa-copy"></i></button>
                        <button onclick="deleteKey('${item.key}')" class="text-danger hover:underline px-1" title="Delete"><i class="fa-solid fa-trash"></i></button>
                    </td>
                </tr>
            `).join('');
        }

        function filterKeys() {
            const q = document.getElementById('gen-search').value.toLowerCase();
            if (!currentUserData || !currentUserData.keys_list) return;
            const filtered = currentUserData.keys_list.filter(i => i.key.toLowerCase().includes(q));
            renderKeysTable(filtered);
        }

        function refreshKeys() {
            verifyKey(currentKey, true);
            showToast('Refreshed');
        }

        async function clearAllKeys() {
            try {
                await fetch('/api/clear-keys', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: currentKey }) });
                verifyKey(currentKey, true);
                showToast('All customer keys cleared');
            } catch (err) {
                showToast('Network error', 'error');
            }
        }

        function renderHistory(list) {
            const tbody = document.getElementById('history-table-body');
            let totalLikes = 0;
            if (list) {
                list.forEach(i => { totalLikes += parseInt(i.given || 0); });
            }
            document.getElementById('history-total-likes').innerText = `TOTAL LIKES : ${totalLikes}`;

            if (!list || list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-txtgray">No records found.</td></tr>`;
                return;
            }
            tbody.innerHTML = list.map(item => `
                <tr class="hover:bg-inputdark/30">
                    <td class="p-2 font-mono">${item.uid}</td>
                    <td class="p-2">${item.nickname}</td>
                    <td class="p-2 text-primary">+${item.given}</td>
                    <td class="p-2 text-txtgray">${item.time}</td>
                    <td class="p-2"><span class="px-2 py-0.5 bg-success/10 text-success rounded text-[8px] font-bold uppercase">Success</span></td>
                </tr>
            `).join('');
        }

        function filterHistory() {
            const q = document.getElementById('history-search').value.toLowerCase();
            if (!currentUserData || !currentUserData.history) return;
            const filtered = currentUserData.history.filter(i => String(i.uid).includes(q) || i.nickname.toLowerCase().includes(q));
            renderHistory(filtered);
        }

        async function clearHistory() {
            await fetch('/api/clear-history', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: currentKey }) });
            verifyKey(currentKey, true);
            showToast('History cleared');
        }

        function logout() {
            sessionStorage.removeItem('ckrpro_key');
            currentKey = '';
            currentUserData = null;
            adminAuthenticated = false;
            document.getElementById('app-view').classList.add('hidden');
            document.getElementById('login-view').classList.remove('hidden');
            showToast('Logged out');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    if not key or key not in DATA_STORE['licenses']:
        return jsonify({"status": 0, "message": "Invalid license key"})
    
    lic = DATA_STORE['licenses'][key]
    is_admin = (lic['type'] == 'admin')

    now_ts = time.time()
    if not is_admin:
        if now_ts > lic['expires']:
            return jsonify({"status": 0, "message": "License expired"})
        remaining_days = max(1, int((lic['expires'] - now_ts) / 86400))
    else:
        remaining_days = "Unlimited"

    auto_expires_str = None
    if lic.get('auto_expires'):
        if lic['auto_expires'] == 'Unlimited':
            auto_expires_str = 'Unlimited'
        else:
            if now_ts > lic['auto_expires']:
                lic['auto_uid'] = None
                lic['auto_expires'] = None
                lic['auto_days'] = None
            else:
                auto_expires_str = datetime.fromtimestamp(lic['auto_expires'], tz=timezone.utc).strftime("%Y-%m-%d")

    keys_list = []
    if is_admin:
        for k, v in DATA_STORE['licenses'].items():
            if v['type'] == 'customer':
                if now_ts <= v['expires']:
                    keys_list.append({
                        "key": v['key'],
                        "duration": v['duration'],
                        "created_at": v['created_at'],
                        "expires_str": datetime.fromtimestamp(v['expires'], tz=timezone.utc).strftime("%Y-%m-%d")
                    })

    return jsonify({
        "status": 1,
        "type": lic['type'],
        "is_admin": is_admin,
        "remaining_days": remaining_days,
        "auto_uid": lic.get('auto_uid'),
        "auto_days_val": lic.get('auto_days'),
        "auto_expires_str": auto_expires_str,
        "stats": {
            "total_requests": DATA_STORE['stats']['total_requests']
        },
        "keys_list": keys_list,
        "history": DATA_STORE['history']
    })

@app.route('/api/verify-admin-pass', methods=['POST'])
def api_verify_admin_pass():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    password = data.get('password', '').strip()
    if key in DATA_STORE['licenses'] and DATA_STORE['licenses'][key]['type'] == 'admin':
        if password == DATA_STORE['admin_password'] or password == key:
            return jsonify({"status": 1})
    return jsonify({"status": 0, "message": "Incorrect Admin Password"})

@app.route('/api/send-likes', methods=['POST'])
def api_send_likes():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    uid = data.get('uid', '').strip()
    server = 'BD'

    if not key or key not in DATA_STORE['licenses']:
        return jsonify({"status": 0, "message": "Unauthorized"})

    lic = DATA_STORE['licenses'][key]
    now_ts = time.time()
    if lic['type'] == 'customer' and now_ts > lic['expires']:
        return jsonify({"status": 0, "message": "License expired"})

    if lic['type'] == 'customer':
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if lic.get('last_used_date') == today_str:
            return jsonify({"status": 0, "message": "You can only use normal likes 1 time per day. Try again tomorrow!"})
        lic['last_used_date'] = today_str

    try:
        api_url = f"https://like-by-ckrpro-api-ob-54.vercel.app/like?uid={uid}&server_name={server}"
        resp = requests.get(api_url, timeout=10)
        api_data = resp.json()
    except Exception:
        DATA_STORE['stats']['total_requests'] += 1
        return jsonify({"status": 0, "message": "API timeout"})

    DATA_STORE['stats']['total_requests'] += 1

    if api_data.get("status") == 1:
        history_entry = {
            "uid": api_data.get("UID"),
            "nickname": api_data.get("PlayerNickname"),
            "given": api_data.get("LikesGivenByAPI", 0),
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }
        DATA_STORE['history'].insert(0, history_entry)
        return jsonify(api_data)
    else:
        return jsonify({"status": 0, "message": "API error"})

@app.route('/api/save-auto-uid', methods=['POST'])
def api_save_auto_uid():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    uid = data.get('uid', '').strip()
    admin_key = data.get('admin_key', '').strip()
    try:
        days = int(data.get('days', 2))
    except (ValueError, TypeError):
        days = 2

    if not key or key not in DATA_STORE['licenses']:
        return jsonify({"status": 0, "message": "Unauthorized"})

    lic = DATA_STORE['licenses'][key]
    now_ts = time.time()

    if lic['type'] == 'admin':
        auto_expires_ts = now_ts + (days * 86400)
        lic['auto_uid'] = uid
        lic['auto_days'] = days
        lic['auto_expires'] = auto_expires_ts
        return jsonify({"status": 1})

    if not admin_key or admin_key not in DATA_STORE['licenses'] or DATA_STORE['licenses'][admin_key]['type'] != 'admin':
        return jsonify({"status": 0, "message": "Invalid Admin Key for Auto-Like setup!"})

    if now_ts > lic['expires']:
        return jsonify({"status": 0, "message": "License expired"})

    auto_expires_ts = now_ts + (days * 86400)
    lic['auto_uid'] = uid
    lic['auto_days'] = days
    lic['auto_expires'] = auto_expires_ts
    return jsonify({"status": 1})

@app.route('/api/generate-key', methods=['POST'])
def api_generate_key():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    if not key or key not in DATA_STORE['licenses'] or DATA_STORE['licenses'][key]['type'] != 'admin':
        return jsonify({"status": 0, "message": "Unauthorized"})

    username = data.get('username', '').strip()
    try:
        days = int(data.get('duration', 30))
    except (ValueError, TypeError):
        days = 30

    if days < 1 or days > 3650:
        return jsonify({"status": 0, "message": "Duration must be between 1 and 3650 days"})

    new_key_str = f"CKR-{username.upper()}-{int(time.time())}" if username else f"CKRPRO-{int(time.time())}"
    expires_time = time.time() + (days * 86400)

    DATA_STORE['licenses'][new_key_str] = {
        "key": new_key_str,
        "type": "customer",
        "duration": f"{days} Days",
        "expires": expires_time,
        "auto_uid": None,
        "auto_expires": None,
        "auto_days": None,
        "last_used_date": None,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }
    return jsonify({"status": 1})

@app.route('/api/delete-key', methods=['POST'])
def api_delete_key():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    target_key = data.get('target_key', '').strip()
    if key in DATA_STORE['licenses'] and DATA_STORE['licenses'][key]['type'] == 'admin':
        if target_key in DATA_STORE['licenses'] and target_key != 'ADMIN-SECRET-SAMU':
            del DATA_STORE['licenses'][target_key]
            return jsonify({"status": 1})
    return jsonify({"status": 0})

@app.route('/api/delete-expired-keys', methods=['POST'])
def api_delete_expired_keys():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    if key in DATA_STORE['licenses'] and DATA_STORE['licenses'][key]['type'] == 'admin':
        now = time.time()
        expired_keys = [k for k, v in DATA_STORE['licenses'].items() if v['type'] == 'customer' and now > v['expires']]
        for ek in expired_keys:
            del DATA_STORE['licenses'][ek]
        return jsonify({"status": 1})
    return jsonify({"status": 0})

@app.route('/api/clear-keys', methods=['POST'])
def api_clear_keys():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    if key in DATA_STORE['licenses'] and DATA_STORE['licenses'][key]['type'] == 'admin':
        DATA_STORE['licenses'] = {
            "ADMIN-SECRET-SAMU": DATA_STORE['licenses']["ADMIN-SECRET-SAMU"]
        }
        return jsonify({"status": 1})
    return jsonify({"status": 0})

@app.route('/api/clear-history', methods=['POST'])
def api_clear_history():
    data = request.get_json() or {}
    if data.get('key') in DATA_STORE['licenses']:
        DATA_STORE['history'] = []
        return jsonify({"status": 1})
    return jsonify({"status": 0})

def scheduled_auto_likes():
    now_ts = time.time()
    for k, lic in list(DATA_STORE['licenses'].items()):
        if lic['type'] == 'customer':
            if now_ts > lic['expires']:
                continue
        
        auto_exp = lic.get('auto_expires')
        if auto_exp and auto_exp != 'Unlimited':
            if now_ts > auto_exp:
                lic['auto_uid'] = None
                lic['auto_expires'] = None
                lic['auto_days'] = None
                continue

        uid = lic.get('auto_uid')
        if uid:
            try:
                api_url = f"https://like-by-ckrpro-api-ob-54.vercel.app/like?uid={uid}&server_name=BD"
                resp = requests.get(api_url, timeout=10)
                api_data = resp.json()
                DATA_STORE['stats']['total_requests'] += 1
                if api_data.get("status") == 1:
                    prefix = "[ADMIN AUTO]" if lic['type'] == 'admin' else "[AUTO]"
                    history_entry = {
                        "uid": api_data.get("UID"),
                        "nickname": f"{prefix} {api_data.get('PlayerNickname')}",
                        "given": api_data.get("LikesGivenByAPI", 0),
                        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    DATA_STORE['history'].insert(0, history_entry)
            except Exception:
                pass

scheduler = BackgroundScheduler()
npt_tz = timezone(timedelta(hours=5, minutes=45))
scheduler.add_job(scheduled_auto_likes, 'cron', hour=8, minute=30, timezone=npt_tz)
scheduler.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
