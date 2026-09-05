"""
Injects PromptCanvas Visual Architecture Studio into portal/static/portal.html:
1. Sidebar button (#tab-promptcanvas-studio)
2. getTabName mapping
3. View container (#view-promptcanvas-studio)
4. Alpine.js state and reactive methods
5. Training gallery slide #1
"""

import sys

PORTAL_HTML_PATH = "portal/static/portal.html"

with open(PORTAL_HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Sidebar Tab Button
sidebar_marker = '<button id="tab-training"'
sidebar_button_code = """          <button id="tab-promptcanvas-studio" @click="currentTab = 'promptcanvas_studio'; if(!promptcanvasRawXml) loadPromptcanvasPreset('option3_dual_plane')" :class="currentTab === 'promptcanvas_studio' ? 'bg-gradient-to-r from-pink-500 via-rose-500 to-amber-500 text-slate-950 font-black shadow-md shadow-pink-500/20' : 'font-semibold hover:text-pink-400 hover:bg-slate-800/20 ring-1 ring-pink-500/20'" :style="currentTab !== 'promptcanvas_studio' ? 'color: var(--color-text-secondary);' : ''" class="w-full px-3 py-2.5 rounded-xl text-xs transition-all flex items-center space-x-3 group" :title="sidebarCollapsed ? '🎨 PromptCanvas Studio' : ''">
            <div class="w-6 h-6 rounded-lg flex items-center justify-center shrink-0" :class="currentTab === 'promptcanvas_studio' ? 'bg-slate-950/20 text-slate-950' : 'text-pink-400 group-hover:scale-110 transition-transform'">
              <i class="fa-solid fa-palette text-sm"></i>
            </div>
            <span x-show="!sidebarCollapsed" class="truncate text-left flex items-center space-x-1.5">
              <span>🎨 PromptCanvas Studio</span>
            </span>
          </button>

          """

if 'id="tab-promptcanvas-studio"' not in html:
    html = html.replace(sidebar_marker, sidebar_button_code + sidebar_marker)
    print("✓ Injected sidebar tab-promptcanvas-studio")

# 2. getTabName mapping
gettab_marker = "'ectd_studio': '🏛️ FDA eCTD 3.2.2 Compiler',"
gettab_code = """'ectd_studio': '🏛️ FDA eCTD 3.2.2 Compiler',
            'promptcanvas_studio': '🎨 PromptCanvas Visual Studio',"""

if "'promptcanvas_studio':" not in html:
    html = html.replace(gettab_marker, gettab_code)
    print("✓ Injected getTabName promptcanvas_studio")

# 3. View Container (#view-promptcanvas-studio)
view_marker = '<div x-show="currentTab === \'training\'"'
view_code = """    <!-- ========================================================================= -->
    <!-- TAB: PROMPTCANVAS VISUAL ARCHITECTURE & DRAW.IO STUDIO                    -->
    <!-- ========================================================================= -->
    <div id="view-promptcanvas-studio" x-show="currentTab === 'promptcanvas_studio'" class="space-y-8">

      <!-- Hero Header Card -->
      <div class="glass-card rounded-3xl p-6 md:p-8 border shadow-xl relative overflow-hidden" style="border-color: var(--color-border-card);">
        <div class="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-pink-500/10 via-rose-500/10 to-amber-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="relative z-10 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
          <div class="space-y-2 max-w-4xl">
            <div class="flex flex-wrap items-center gap-2">
              <span class="px-3 py-1 rounded-lg text-xs font-black bg-gradient-to-r from-pink-500/20 via-rose-500/20 to-amber-500/20 text-pink-400 border border-pink-500/30 uppercase tracking-widest flex items-center gap-1.5">
                <i class="fa-solid fa-shapes"></i> PromptCanvas ⟷ A2A Visual Bridge
              </span>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-pink-500/20 text-pink-400 border border-pink-500/30">
                Draw.io mxGraphModel
              </span>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                1-Click DAG Synthesis
              </span>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                Auto Collision Healing
              </span>
            </div>
            <h1 class="text-2xl md:text-3xl lg:text-4xl font-black tracking-tight" style="color: var(--color-text-primary);">
              PromptCanvas Visual Architecture & Draw.io Studio
            </h1>
            <p class="text-xs md:text-sm leading-relaxed max-w-3xl" style="color: var(--color-text-secondary);">
              Visually design sovereign biopharma agent swarms and enterprise topologies in Draw.io / PromptCanvas format. 1-Click compile mxGraphModel XML into live executable A2A Gateway DAGs with automated AST sanitization and 21 CFR Part 11 validation.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button id="btn-export-drawio" @click="exportPromptcanvasXml()" class="px-4 py-2.5 rounded-xl border font-bold text-xs flex items-center space-x-2 transition-all hover:border-pink-400" style="background-color: var(--color-bg-card-subtle); border-color: var(--color-border-card); color: var(--color-text-primary);">
              <i class="fa-solid fa-file-arrow-down text-pink-400"></i>
              <span>Download .drawio</span>
            </button>
            <button id="btn-compile-promptcanvas-dag" @click="compilePromptcanvasArchitecture()" :disabled="promptcanvasCompiling" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 via-rose-500 to-amber-500 text-slate-950 font-black text-xs shadow-lg shadow-pink-500/20 hover:opacity-95 transition-all flex items-center space-x-2">
              <i class="fa-solid fa-wand-magic-sparkles"></i>
              <span x-text="promptcanvasCompiling ? 'Compiling DAG...' : 'Compile Architecture to A2A DAG'"></span>
            </button>
          </div>
        </div>
      </div>

      <!-- Quick Metrics Ribbon -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="glass-card rounded-2xl p-4 border space-y-1" style="border-color: var(--color-border-card);">
          <div class="text-[10px] font-mono uppercase font-bold text-pink-400 flex items-center justify-between">
            <span>Visual Conversion</span>
            <i class="fa-solid fa-bolt"></i>
          </div>
          <div class="text-xl font-black" style="color: var(--color-text-primary);">&lt; 15 µs</div>
          <div class="text-[11px]" style="color: var(--color-text-muted);">In-Memory ElementTree</div>
        </div>
        <div class="glass-card rounded-2xl p-4 border space-y-1" style="border-color: var(--color-border-card);">
          <div class="text-[10px] font-mono uppercase font-bold text-emerald-400 flex items-center justify-between">
            <span>Standard Protocol</span>
            <i class="fa-solid fa-diagram-project"></i>
          </div>
          <div class="text-xl font-black" style="color: var(--color-text-primary);">Google A2A v1.0</div>
          <div class="text-[11px]" style="color: var(--color-text-muted);">Typed Protobuf / gRPC</div>
        </div>
        <div class="glass-card rounded-2xl p-4 border space-y-1" style="border-color: var(--color-border-card);">
          <div class="text-[10px] font-mono uppercase font-bold text-cyan-400 flex items-center justify-between">
            <span>Collision Guard</span>
            <i class="fa-solid fa-arrows-to-dot"></i>
          </div>
          <div class="text-xl font-black" style="color: var(--color-text-primary);">30px Margin</div>
          <div class="text-[11px]" style="color: var(--color-text-muted);">2D Bounding Box Auto-Heal</div>
        </div>
        <div class="glass-card rounded-2xl p-4 border space-y-1" style="border-color: var(--color-border-card);">
          <div class="text-[10px] font-mono uppercase font-bold text-amber-400 flex items-center justify-between">
            <span>Regulatory Ledger</span>
            <i class="fa-solid fa-stamp"></i>
          </div>
          <div class="text-xl font-black" style="color: var(--color-text-primary);">21 CFR Part 11</div>
          <div class="text-[11px]" style="color: var(--color-text-muted);">Automatic Merkle Chaining</div>
        </div>
      </div>

      <!-- Archetype Preset Selector Bar -->
      <div class="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl border" style="background-color: var(--color-bg-card); border-color: var(--color-border-card);">
        <div class="flex items-center space-x-2">
          <span class="text-xs font-bold" style="color: var(--color-text-secondary);">Architecture Preset:</span>
          <button @click="loadPromptcanvasPreset('option3_dual_plane')" :class="promptcanvasActivePreset === 'option3_dual_plane' ? 'bg-pink-500 text-slate-950 font-black shadow-md' : 'border font-semibold hover:border-pink-400'" :style="promptcanvasActivePreset !== 'option3_dual_plane' ? 'background-color: var(--color-bg-card-subtle); border-color: var(--color-border-subtle); color: var(--color-text-secondary);' : ''" class="px-3.5 py-1.5 rounded-xl text-xs transition-all flex items-center space-x-1.5">
            <i class="fa-solid fa-shield-halved"></i>
            <span>Option 3: Dual-Plane PSC (Sovereign Enclave)</span>
          </button>
          <button @click="loadPromptcanvasPreset('option1_cloud_run')" :class="promptcanvasActivePreset === 'option1_cloud_run' ? 'bg-cyan-500 text-slate-950 font-black shadow-md' : 'border font-semibold hover:border-cyan-400'" :style="promptcanvasActivePreset !== 'option1_cloud_run' ? 'background-color: var(--color-bg-card-subtle); border-color: var(--color-border-subtle); color: var(--color-text-secondary);' : ''" class="px-3.5 py-1.5 rounded-xl text-xs transition-all flex items-center space-x-1.5">
            <i class="fa-solid fa-cloud"></i>
            <span>Option 1: Cloud Run Proxy Interceptor</span>
          </button>
        </div>
        <div class="text-xs font-mono text-emerald-400 font-bold flex items-center space-x-1.5">
          <i class="fa-solid fa-circle-check"></i>
          <span>Draw.io XML Ready</span>
        </div>
      </div>

      <!-- Main Two-Column Layout -->
      <div class="grid grid-cols-1 xl:grid-cols-12 gap-8">

        <!-- Left Column: Visual Diagram Canvas & Interactive Node Inspector (7 Cols) -->
        <div class="xl:col-span-7 space-y-6">

          <!-- Interactive SVG Architectural Diagram Viewer -->
          <div class="glass-card rounded-3xl p-6 border space-y-4" style="border-color: var(--color-border-card);">
            <div class="flex items-center justify-between border-b pb-3" style="border-color: var(--color-border-subtle);">
              <div>
                <span class="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-pink-500/20 text-pink-400 uppercase tracking-wider">Visual Graph Viewport</span>
                <h3 class="text-sm font-black mt-0.5" style="color: var(--color-text-primary);">Interactive Architecture Topology (PromptCanvas Render)</h3>
              </div>
              <span class="font-mono text-[11px] text-cyan-400 font-bold">12 Verified Nodes</span>
            </div>

            <!-- SVG Diagram Canvas -->
            <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800 relative overflow-hidden">
              <svg viewBox="0 0 760 380" class="w-full h-auto text-slate-200 select-none">
                <defs>
                  <linearGradient id="gradSovereign" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#064e3b" stop-opacity="0.3"/>
                    <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
                  </linearGradient>
                  <linearGradient id="gradExternal" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#1e1b4b" stop-opacity="0.3"/>
                    <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
                  </linearGradient>
                  <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1 L 8 5 L 0 9 z" fill="#38bdf8" />
                  </marker>
                  <marker id="arrowGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981" />
                  </marker>
                </defs>

                <!-- Swimlane 1: Sovereign Biopharma VPC -->
                <rect x="20" y="20" width="340" height="340" rx="16" fill="url(#gradSovereign)" stroke="#10b981" stroke-width="1.5" stroke-dasharray="6 4" />
                <text x="35" y="45" fill="#34d399" font-size="11" font-family="sans-serif" font-weight="900" letter-spacing="0.5">SOVEREIGN BIOPHARMA VPC</text>

                <!-- Swimlane 2: Gemini Enterprise Workspace -->
                <rect x="400" y="20" width="340" height="340" rx="16" fill="url(#gradExternal)" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="6 4" />
                <text x="415" y="45" fill="#38bdf8" font-size="11" font-family="sans-serif" font-weight="900" letter-spacing="0.5">GEMINI ENTERPRISE WORKSPACE</text>

                <!-- Nodes in Sovereign Enclave -->
                <g @click="selectPromptcanvasNode({id: 'node_clinical_db', name: 'CDISC SDTM Lakehouse', type: 'STORAGE_RESIDENCY', latency: '15 ms', clearance: '21 CFR Part 11', desc: 'Secure repository for clinical subject cohorts.'})" class="cursor-pointer group">
                  <rect x="40" y="65" width="135" height="60" rx="10" fill="#1e293b" stroke="#059669" stroke-width="1.5" class="hover:stroke-emerald-400 transition-colors"/>
                  <text x="50" y="88" fill="#e2e8f0" font-size="10" font-family="sans-serif" font-weight="bold">CDISC SDTM Lake</text>
                  <text x="50" y="105" fill="#94a3b8" font-size="8" font-family="monospace">BigQuery RLS / AES</text>
                </g>

                <g @click="selectPromptcanvasNode({id: 'node_agent_swarm', name: 'Sovereign Agents (10K Twins)', type: 'REASONING_SWARM', latency: '12.8 ms', clearance: 'RESTRICTED', desc: 'Vectorized in-silico patient simulation pod.'})" class="cursor-pointer group">
                  <rect x="40" y="155" width="135" height="60" rx="10" fill="#1e293b" stroke="#10b981" stroke-width="1.5" class="hover:stroke-emerald-400 transition-colors"/>
                  <text x="50" y="178" fill="#e2e8f0" font-size="10" font-family="sans-serif" font-weight="bold">10K Digital Twins</text>
                  <text x="50" y="195" fill="#94a3b8" font-size="8" font-family="monospace">PK/PD Swarm Engine</text>
                </g>

                <g @click="selectPromptcanvasNode({id: 'node_ast_sanitizer', name: 'Sub-28µs AST Sanitizer', type: 'IN_MEMORY_FILTER', latency: '5.95 µs', clearance: 'ENCLAVE_HOTPATH', desc: 'Strips prohibited envelopes without regular expressions.'})" class="cursor-pointer group">
                  <rect x="205" y="155" width="135" height="60" rx="10" fill="#0284c7" stroke="#38bdf8" stroke-width="2" class="hover:stroke-cyan-300 transition-colors"/>
                  <text x="215" y="178" fill="#ffffff" font-size="10" font-family="sans-serif" font-weight="bold">AST Sanitizer</text>
                  <text x="215" y="195" fill="#bae6fd" font-size="8" font-family="monospace">5.95 µs (No ReDoS)</text>
                </g>

                <g @click="selectPromptcanvasNode({id: 'node_psc_producer', name: 'PSC Producer (mTLS 1.3)', type: 'ZERO_EGRESS_NETWORK', latency: '850 µs', clearance: 'ENTERPRISE_PEERING', desc: 'Private Service Connect internal load balancer.'})" class="cursor-pointer group">
                  <rect x="205" y="260" width="135" height="60" rx="10" fill="#064e3b" stroke="#34d399" stroke-width="1.5" class="hover:stroke-emerald-300 transition-colors"/>
                  <text x="215" y="283" fill="#ffffff" font-size="10" font-family="sans-serif" font-weight="bold">PSC Producer ILB</text>
                  <text x="215" y="300" fill="#a7f3d0" font-size="8" font-family="monospace">Port 50051 (mTLS)</text>
                </g>

                <!-- Interconnect Bridge Line (Zero Egress Tunnel) -->
                <path d="M 340 290 L 420 290" stroke="#00f2fe" stroke-width="3" stroke-dasharray="4 2" marker-end="url(#arrow)" />
                <text x="345" y="280" fill="#00f2fe" font-size="8" font-family="monospace" font-weight="bold">PSC Peering</text>

                <!-- Nodes in External Workspace -->
                <g @click="selectPromptcanvasNode({id: 'node_psc_consumer', name: 'PSC Consumer Endpoint', type: 'ZERO_EGRESS_NETWORK', latency: '200 µs', clearance: 'INTERNAL_IP', desc: 'Forwarding rule to 10.128.0.50 without internet gateway.'})" class="cursor-pointer group">
                  <rect x="420" y="260" width="135" height="60" rx="10" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5" class="hover:stroke-cyan-400 transition-colors"/>
                  <text x="430" y="283" fill="#e2e8f0" font-size="10" font-family="sans-serif" font-weight="bold">PSC Consumer</text>
                  <text x="430" y="300" fill="#94a3b8" font-size="8" font-family="monospace">10.128.0.50 (No IP)</text>
                </g>

                <g @click="selectPromptcanvasNode({id: 'node_vertex_gemini', name: 'Vertex AI Gemini 2.5 Pro', type: 'REASONING_SWARM', latency: '450 ms', clearance: 'ORCHESTRATOR', desc: 'Google ADK Protocol reasoning engine.'})" class="cursor-pointer group">
                  <rect x="420" y="65" width="135" height="60" rx="10" fill="#581c87" stroke="#c084fc" stroke-width="1.5" class="hover:stroke-purple-300 transition-colors"/>
                  <text x="430" y="88" fill="#ffffff" font-size="10" font-family="sans-serif" font-weight="bold">Vertex Gemini 2.5</text>
                  <text x="430" y="105" fill="#e9d5ff" font-size="8" font-family="monospace">ADK Orchestrator</text>
                </g>

                <g @click="selectPromptcanvasNode({id: 'node_a2ui_renderer', name: 'Universal A2UI Transpiler', type: 'OMNICHANNEL_SURFACE', latency: '1.4 ms', clearance: 'HITL_HUMAN', desc: 'Translates to Google Chat, Slack, and Web cards with JTI nonce.'})" class="cursor-pointer group">
                  <rect x="585" y="65" width="135" height="60" rx="10" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5" class="hover:stroke-cyan-400 transition-colors"/>
                  <text x="595" y="88" fill="#e2e8f0" font-size="10" font-family="sans-serif" font-weight="bold">A2UI Transpiler</text>
                  <text x="595" y="105" fill="#94a3b8" font-size="8" font-family="monospace">Omnichannel Cards</text>
                </g>

                <g @click="selectPromptcanvasNode({id: 'node_ectd_engine', name: '1-Click FDA eCTD Compiler', type: 'REGULATORY_DOSSIER', latency: '22 ms', clearance: 'FDA_ESG_DIRECT', desc: 'Synthesizes Form FDA 1571/1572 & § 11.70 Merkle Root.'})" class="cursor-pointer group">
                  <rect x="585" y="155" width="135" height="60" rx="10" fill="#7c2d12" stroke="#fb923c" stroke-width="2" class="hover:stroke-orange-300 transition-colors"/>
                  <text x="595" y="178" fill="#ffffff" font-size="10" font-family="sans-serif" font-weight="bold">FDA eCTD 3.2.2</text>
                  <text x="595" y="195" fill="#fed7aa" font-size="8" font-family="monospace">&lt; 25 ms Packaging</text>
                </g>

                <g @click="selectPromptcanvasNode({id: 'node_hitl_reviewer', name: 'Principal Investigator (HITL)', type: 'CRYPTOGRAPHIC_GUARD', latency: '48h TTL', clearance: 'PI_CREDENTIALS', desc: 'Stateless HMAC-SHA256 human-in-the-loop approval.'})" class="cursor-pointer group">
                  <rect x="585" y="260" width="135" height="60" rx="10" fill="#1e293b" stroke="#10b981" stroke-width="1.5" class="hover:stroke-emerald-400 transition-colors"/>
                  <text x="595" y="283" fill="#e2e8f0" font-size="10" font-family="sans-serif" font-weight="bold">Dr. Sarah Chen, MD</text>
                  <text x="595" y="300" fill="#94a3b8" font-size="8" font-family="monospace">1-Click HMAC Sign</text>
                </g>

                <!-- Internal Connections -->
                <path d="M 107 125 L 107 155" stroke="#10b981" stroke-width="1.5" marker-end="url(#arrowGreen)" />
                <path d="M 175 185 L 205 185" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow)" />
                <path d="M 272 215 L 272 260" stroke="#10b981" stroke-width="1.5" marker-end="url(#arrowGreen)" />
                <path d="M 487 260 L 487 125" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow)" />
                <path d="M 555 95 L 585 95" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrow)" />
                <path d="M 652 125 L 652 155" stroke="#fb923c" stroke-width="1.5" marker-end="url(#arrow)" />
                <path d="M 652 215 L 652 260" stroke="#10b981" stroke-width="1.5" marker-end="url(#arrowGreen)" />
              </svg>
            </div>
          </div>

          <!-- Live Node Inspector Card -->
          <div class="glass-card rounded-3xl p-6 border space-y-4" style="border-color: var(--color-border-card);">
            <div class="flex items-center justify-between border-b pb-3" style="border-color: var(--color-border-subtle);">
              <h3 class="text-sm font-black" style="color: var(--color-text-primary);">Node Inspector (PromptCanvas Metadata)</h3>
              <span class="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-pink-500/20 text-pink-400" x-text="promptcanvasSelectedNode ? promptcanvasSelectedNode.type : 'CLICK ANY NODE ABOVE'"></span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div class="p-3 rounded-xl border space-y-1" style="background-color: var(--color-bg-card-subtle); border-color: var(--color-border-subtle);">
                <div class="text-[10px] font-mono text-slate-400 font-bold uppercase">COMPONENT NAME</div>
                <div class="font-bold text-sm" style="color: var(--color-text-primary);" x-text="promptcanvasSelectedNode ? promptcanvasSelectedNode.name : 'Sub-28µs AST Sanitizer'"></div>
              </div>
              <div class="p-3 rounded-xl border space-y-1" style="background-color: var(--color-bg-card-subtle); border-color: var(--color-border-subtle);">
                <div class="text-[10px] font-mono text-slate-400 font-bold uppercase">LATENCY BUDGET</div>
                <div class="font-mono font-bold text-cyan-400 text-sm" x-text="promptcanvasSelectedNode ? promptcanvasSelectedNode.latency : '5.95 µs'"></div>
              </div>
              <div class="p-3 rounded-xl border space-y-1" style="background-color: var(--color-bg-card-subtle); border-color: var(--color-border-subtle);">
                <div class="text-[10px] font-mono text-slate-400 font-bold uppercase">SECURITY TIER</div>
                <div class="font-mono font-bold text-emerald-400 text-sm" x-text="promptcanvasSelectedNode ? promptcanvasSelectedNode.clearance : 'ENCLAVE_HOTPATH'"></div>
              </div>
            </div>

            <div class="p-3 rounded-xl border text-xs" style="background-color: var(--color-bg-card-subtle); border-color: var(--color-border-subtle);">
              <span class="font-mono text-[10px] text-slate-400 uppercase font-bold">SPECIFICATION: </span>
              <span style="color: var(--color-text-secondary);" x-text="promptcanvasSelectedNode ? promptcanvasSelectedNode.desc : 'Filters outbound payloads leaving internal sovereign biopharma enclaves in memory in under 28 microseconds with zero regular-expression backtracking.'"></span>
            </div>
          </div>

        </div>

        <!-- Right Column: Compiled A2A DAG & Draw.io XML (5 Cols) -->
        <div class="xl:col-span-5 space-y-6">

          <!-- Compiled DAG Execution Plan -->
          <div class="glass-card rounded-3xl p-6 border space-y-4" style="border-color: var(--color-border-card);">
            <div class="flex items-center justify-between border-b pb-3" style="border-color: var(--color-border-subtle);">
              <div>
                <h3 class="text-sm font-black" style="color: var(--color-text-primary);">Synthesized A2A DAG Plan</h3>
                <div class="text-[11px] font-mono text-pink-400" x-text="promptcanvasCompiledDag ? promptcanvasCompiledDag.dag_id : 'Awaiting 1-Click Synthesis'"></div>
              </div>
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400" x-text="promptcanvasCompiledDag ? '✓ Compiled (' + promptcanvasCompiledDag.nodes_count + ' Stages)' : 'Ready'"></span>
            </div>

            <!-- Stage List -->
            <div class="space-y-2 max-h-64 overflow-y-auto custom-scrollbar pr-1 text-xs">
              <template x-for="(stage, idx) in (promptcanvasCompiledDag ? promptcanvasCompiledDag.execution_plan : promptcanvasDefaultStages)" :key="idx">
                <div class="p-2.5 rounded-xl border flex items-center justify-between transition-all hover:border-pink-400/50" style="background-color: var(--color-bg-card-subtle); border-color: var(--color-border-subtle);">
                  <div class="flex items-center space-x-2.5 truncate">
                    <span class="w-5 h-5 rounded-full bg-pink-500/20 text-pink-400 text-[10px] font-mono font-bold flex items-center justify-center shrink-0" x-text="stage.stage_index"></span>
                    <span class="font-bold truncate" style="color: var(--color-text-primary);" x-text="stage.label"></span>
                  </div>
                  <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-cyan-300 shrink-0" x-text="stage.expected_latency_us + ' µs'"></span>
                </div>
              </template>
            </div>

            <!-- Action Bridge to DAG Studio -->
            <button id="btn-bridge-to-dag-studio" @click="currentTab = 'dag_studio'" class="w-full py-2.5 rounded-xl border font-black text-xs flex items-center justify-center space-x-2 transition-all hover:border-cyan-400" style="background-color: var(--color-bg-card-subtle); border-color: var(--color-border-card); color: var(--color-text-primary);">
              <i class="fa-solid fa-arrow-up-right-from-square text-cyan-400"></i>
              <span>Open Synthesized Mesh in Drag & Drop DAG Studio</span>
            </button>
          </div>

          <!-- Raw Draw.io XML Code Box -->
          <div class="glass-card rounded-3xl p-6 border space-y-4" style="border-color: var(--color-border-card);">
            <div class="flex items-center justify-between border-b pb-3" style="border-color: var(--color-border-subtle);">
              <h3 class="text-sm font-black" style="color: var(--color-text-primary);">Draw.io mxGraphModel XML</h3>
              <button id="btn-copy-drawio-xml" @click="copyPromptcanvasXml()" class="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-pink-400 text-[11px] font-mono font-bold transition-all flex items-center space-x-1">
                <i class="fa-solid fa-copy"></i>
                <span x-text="promptcanvasXmlCopied ? 'Copied!' : 'Copy XML'"></span>
              </button>
            </div>

            <pre class="p-3.5 rounded-xl bg-slate-950 text-slate-200 font-mono text-[10px] leading-relaxed overflow-x-auto max-h-52 custom-scrollbar border border-slate-800"><code x-text="promptcanvasRawXml || 'Loading PromptCanvas XML...'"></code></pre>
          </div>

        </div>

      </div>

    </div>

"""

if 'id="view-promptcanvas-studio"' not in html:
    html = html.replace(view_marker, view_code + "\n    " + view_marker)
    print("✓ Injected view-promptcanvas-studio container")

# 4. Alpine State Variables
state_marker = "ectdXmlCopied: false,"
state_code = """ectdXmlCopied: false,
        // PromptCanvas Studio State
        promptcanvasActivePreset: 'option3_dual_plane',
        promptcanvasSelectedNode: null,
        promptcanvasCompiledDag: null,
        promptcanvasCompiling: false,
        promptcanvasXmlCopied: false,
        promptcanvasRawXml: '',
        promptcanvasDefaultStages: [
          { stage_index: 1, label: 'CDISC SDTM Lakehouse', type: 'STORAGE_RESIDENCY', expected_latency_us: 15000 },
          { stage_index: 2, label: '10K Digital Twins Swarm', type: 'REASONING_SWARM', expected_latency_us: 12840 },
          { stage_index: 3, label: 'Sub-28µs AST Sanitizer', type: 'IN_MEMORY_FILTER', expected_latency_us: 6 },
          { stage_index: 4, label: 'PSC Producer ILB (mTLS)', type: 'ZERO_EGRESS_NETWORK', expected_latency_us: 850 },
          { stage_index: 5, label: 'PSC Consumer Endpoint', type: 'ZERO_EGRESS_NETWORK', expected_latency_us: 200 },
          { stage_index: 6, label: 'Vertex AI Gemini 2.5 Pro', type: 'REASONING_SWARM', expected_latency_us: 450000 },
          { stage_index: 7, label: 'Universal A2UI Transpiler', type: 'OMNICHANNEL_SURFACE', expected_latency_us: 1400 },
          { stage_index: 8, label: '1-Click FDA eCTD Compiler', type: 'REGULATORY_DOSSIER', expected_latency_us: 22000 },
          { stage_index: 9, label: 'Principal Investigator (HITL)', type: 'CRYPTOGRAPHIC_GUARD', expected_latency_us: 120 }
        ],"""

if "promptcanvasActivePreset:" not in html:
    html = html.replace(state_marker, state_code)
    print("✓ Injected Alpine promptcanvas state variables")

# 5. Alpine Methods
method_marker = "downloadEctdBundle() {"
methods_code = """async loadPromptcanvasPreset(presetKey) {
          this.promptcanvasActivePreset = presetKey;
          try {
            const res = await fetch(`/api/promptcanvas/diagram/${presetKey}`);
            const data = await res.json();
            this.promptcanvasRawXml = data.drawioXml;
          } catch(e) {
            console.error('Failed to load diagram preset:', e);
          }
        },
        async compilePromptcanvasArchitecture() {
          this.promptcanvasCompiling = true;
          try {
            if (!this.promptcanvasRawXml) {
              await this.loadPromptcanvasPreset(this.promptcanvasActivePreset);
            }
            const res = await fetch('/api/promptcanvas/compile-to-dag', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                drawio_xml: this.promptcanvasRawXml,
                target_protocol: 'a2a.v1.0.0',
                enforce_ast_sanitization: true
              })
            });
            this.promptcanvasCompiledDag = await res.json();
          } catch(e) {
            console.error('DAG compilation error:', e);
          } finally {
            this.promptcanvasCompiling = false;
          }
        },
        selectPromptcanvasNode(node) {
          this.promptcanvasSelectedNode = node;
        },
        copyPromptcanvasXml() {
          navigator.clipboard.writeText(this.promptcanvasRawXml);
          this.promptcanvasXmlCopied = true;
          setTimeout(() => { this.promptcanvasXmlCopied = false; }, 2500);
        },
        exportPromptcanvasXml() {
          const blob = new Blob([this.promptcanvasRawXml], { type: 'application/xml' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `A2A_Gateway_${this.promptcanvasActivePreset}.drawio`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        },
        """

if "compilePromptcanvasArchitecture()" not in html:
    html = html.replace(method_marker, methods_code + method_marker)
    print("✓ Injected Alpine promptcanvas methods")

# 6. Training Gallery Slide
training_marker = "title: 'Flagship: 1-Click FDA eCTD 3.2.2 Automated Regulatory Compiler',"
training_slide_code = """{
            step: 10,
            title: 'Visual Architecture Studio: PromptCanvas ⟷ A2A Sovereign Bridge',
            subtitle: 'Draw.io mxGraphModel Compilation, 1-Click DAG Synthesis & 2D Collision Healing',
            darkImg: '/static/screenshots/dark_promptcanvas_01_studio.png',
            lightImg: '/static/screenshots/light_promptcanvas_01_studio.png',
            badge: 'PromptCanvas Bridge',
            desc: 'Visual multi-agent topology designer: Ingests Draw.io mxGraphModel XML diagrams and synthesizes live executable A2A Gateway DAGs with automated AST sanitization and 21 CFR Part 11 validation.'
          },
          """

if "PromptCanvas ⟷ A2A Sovereign Bridge" not in html:
    html = html.replace(training_marker, training_slide_code + training_marker)
    print("✓ Injected PromptCanvas training slide")

with open(PORTAL_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("🚀 Successfully injected PromptCanvas Visual Architecture Studio into portal/static/portal.html!")
