import sys
import re

with open('portal/static/portal.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add sidebar button before #tab-training
sidebar_target = '<button id="tab-training"'
sidebar_replacement = '''<button id="tab-advanced-lab" @click="currentTab = 'advanced_a2a_lab'" :class="currentTab === 'advanced_a2a_lab' ? 'bg-gradient-to-r from-cyan-500 via-teal-500 to-indigo-500 text-slate-950 font-black shadow-md shadow-cyan-500/20' : 'font-semibold hover:text-cyan-400 hover:bg-slate-800/20 ring-1 ring-cyan-500/20'" :style="currentTab !== 'advanced_a2a_lab' ? 'color: var(--color-text-secondary);' : ''" class="w-full px-3 py-2.5 rounded-xl text-xs transition-all flex items-center space-x-3 group" :title="sidebarCollapsed ? '⚡ Advanced A2A Lab' : ''">
            <div class="w-6 h-6 rounded-lg flex items-center justify-center shrink-0" :class="currentTab === 'advanced_a2a_lab' ? 'bg-slate-950/20 text-slate-950' : 'text-cyan-400 group-hover:scale-110 transition-transform'">
              <i class="fa-solid fa-atom text-sm"></i>
            </div>
            <span x-show="!sidebarCollapsed" class="truncate text-left flex items-center space-x-1.5">
              <span>⚡ Advanced A2A Lab</span>
            </span>
          </button>

          <button id="tab-training"'''

if sidebar_target in content:
    content = content.replace(sidebar_target, sidebar_replacement, 1)
    print("✅ Successfully injected sidebar button #tab-advanced-lab")
else:
    print("❌ Could not find sidebar_target!")
    sys.exit(1)

with open('portal/static/portal.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved step 1")
