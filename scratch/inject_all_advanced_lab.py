import sys

with open('portal/static/portal.html', 'r', encoding='utf-8') as f:
    content = f.read()

with open('scratch/advanced_lab_view.html', 'r', encoding='utf-8') as f:
    view_html = f.read()

# 1. Insert view_html right before Training tab
training_target = '    <!-- ========================================================================= -->\n    <!-- TAB: GEMINI ENTERPRISE USER TRAINING & ONBOARDING HUB                     -->'
if training_target not in content:
    print("❌ Could not find training_target!")
    sys.exit(1)

content = content.replace(training_target, view_html + '\n\n' + training_target, 1)
print("✅ Injected view_html before training tab")

# 2. Inject reactive state variables into portalState()
state_target = "        // Futuristic Landing Page Quantum State"
state_vars = '''        // Advanced A2A Protocol Lab Reactive State
        advancedLabTab: 'mcp_bridge',
        mcpClientType: 'claude_mcp',
        mcpToolName: 'titrate_clinical_dose',
        mcpStudyId: 'MK-3475-087',
        mcpCohort: 'Cohort-B',
        mcpDoseMg: 280,
        mcpExecuting: false,
        mcpBridgeResult: null,

        quorumAmendmentId: 'AMD-ONC-2026-08',
        quorumProposedDose: 300,
        quorumRule: 'majority',
        quorumEvaluating: false,
        quorumResult: null,

        multisigCertificateId: 'CERT-2026-GxP-09',
        multisigTiersSigned: { 1: false, 2: false, 3: false },
        multisigSignatures: { 1: null, 2: null, 3: null },
        multisigSigning: false,

        streamSteeringPrompt: 'Restrict cohort to Age < 65 and enforce Day 7 AST telemetry',
        streamSteerConstraint: 'Max Dose <= 250mg & Mandatory Day 7 Liver Panel',
        streamSteerInjected: false,
        streamSteerResult: null,
        checkpointToken: 'chkpt-aip127-9941a2f0',
        checkpointStatus: 'IDLE',

        enclaveReport: null,
        zkpCohortSize: 340,
        zkpMinAge: 18,
        zkpMaxBilirubin: 1.5,
        zkpVerifying: false,
        zkpResult: null,

        traceWaterfallData: null,
        chaosInjectionType: 'jitter',
        chaosSeverity: 65,
        chaosSimulating: false,
        chaosResult: null,
        dlqRetried: false,

'''

if state_target not in content:
    print("❌ Could not find state_target!")
    sys.exit(1)

content = content.replace(state_target, state_vars + state_target, 1)
print("✅ Injected reactive state variables")

# 3. Inject reactive methods right before init() {
init_target = "        init() {"
methods = '''        async executeMcpBridge() {
          this.mcpExecuting = true;
          try {
            const resp = await fetch('/api/mcp/convert-and-execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                client_type: this.mcpClientType,
                tool_name: this.mcpToolName,
                arguments: {
                  study_id: this.mcpStudyId,
                  cohort: this.mcpCohort,
                  target_dose_mg: this.mcpDoseMg,
                  justification: 'Bayesian safety variance review'
                }
              })
            });
            this.mcpBridgeResult = await resp.json();
          } catch (e) {
            console.error('MCP Bridge execution failed:', e);
          } finally {
            this.mcpExecuting = false;
          }
        },

        async evaluateQuorumVote() {
          this.quorumEvaluating = true;
          try {
            const resp = await fetch('/api/quorum/evaluate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                amendment_id: this.quorumAmendmentId,
                proposed_dose_mg: this.quorumProposedDose,
                quorum_rule: this.quorumRule
              })
            });
            this.quorumResult = await resp.json();
          } catch (e) {
            console.error('Quorum vote evaluation failed:', e);
          } finally {
            this.quorumEvaluating = false;
          }
        },

        async signMultiSigTier(tier) {
          const signers = {
            1: { name: 'Dr. Marcus Vance, MD', role: 'Principal Investigator (Site 104)', meaning: 'Trial Site Investigation and Patient Baseline Safety Review' },
            2: { name: 'Dr. Sarah Chen, PhD', role: 'Lead Clinical Biostatistician', meaning: 'Bayesian Hazard Ratio and Statistical Efficacy Verification' },
            3: { name: 'Dr. Evelyn Reed, MD', role: 'Global Medical Review Director', meaning: 'Global Medical Approval & 21 CFR Part 11 Electronic Seal Execution' }
          };
          const info = signers[tier];
          const prevHash = (tier === 1) ? 'GENESIS_0000000000000000000000000000000000000000' : (this.multisigSignatures[tier - 1]?.currentHash || 'HASH_TIER_PREV');
          
          try {
            const resp = await fetch('/api/multisig/sign-tier', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                certificate_id: this.multisigCertificateId,
                tier: tier,
                signer_name: info.name,
                signer_role: info.role,
                meaning: info.meaning,
                previous_hash: prevHash,
                amendment_data: { study: 'MK-3475-087', dose: 280 }
              })
            });
            const data = await resp.json();
            this.multisigSignatures[tier] = data;
            this.multisigTiersSigned[tier] = true;
            if (tier === 3 && typeof confetti === 'function') {
              confetti({ particleCount: 80, spread: 70, origin: { y: 0.6 } });
            }
          } catch (e) {
            console.error('MultiSig sign failed:', e);
          }
        },

        resetMultiSigChain() {
          this.multisigTiersSigned = { 1: false, 2: false, 3: false };
          this.multisigSignatures = { 1: null, 2: null, 3: null };
        },

        async injectInFlightSteering() {
          this.streamSteerInjected = true;
          try {
            const resp = await fetch('/api/streaming/steer', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                task_id: 'task-steer-941',
                steering_prompt: this.streamSteeringPrompt,
                target_constraint: this.streamSteerConstraint
              })
            });
            this.streamSteerResult = await resp.json();
          } catch (e) {
            console.error('Steer failed:', e);
          }
        },

        async createAip127Checkpoint() {
          this.checkpointStatus = 'PAUSED';
          try {
            const resp = await fetch('/api/streaming/checkpoint', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ task_id: 'task-steer-941', action: 'snapshot' })
            });
            const data = await resp.json();
            this.checkpointToken = data.checkpointToken;
          } catch (e) {
            console.error('Checkpoint snapshot failed:', e);
          }
        },

        async resumeAip127Checkpoint() {
          this.checkpointStatus = 'RESUMED';
          try {
            await fetch('/api/streaming/checkpoint', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ task_id: 'task-steer-941', action: 'resume', checkpoint_token: this.checkpointToken })
            });
          } catch (e) {
            console.error('Checkpoint resume failed:', e);
          }
        },

        async fetchEnclaveAttestation() {
          try {
            const resp = await fetch('/api/enclave/attestation-report');
            this.enclaveReport = await resp.json();
          } catch (e) {
            console.error('Enclave report failed:', e);
          }
        },

        async verifyZkpProof() {
          this.zkpVerifying = true;
          try {
            const resp = await fetch('/api/enclave/verify-zkp', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                cohort_size: this.zkpCohortSize,
                min_age_threshold: this.zkpMinAge,
                max_bilirubin_mg_dl: this.zkpMaxBilirubin
              })
            });
            this.zkpResult = await resp.json();
          } catch (e) {
            console.error('ZKP verification failed:', e);
          } finally {
            this.zkpVerifying = false;
          }
        },

        async fetchTraceWaterfall() {
          try {
            const resp = await fetch('/api/telemetry/distributed-trace');
            this.traceWaterfallData = await resp.json();
          } catch (e) {
            console.error('Trace fetch failed:', e);
          }
        },

        async simulateChaosFault() {
          this.chaosSimulating = true;
          this.dlqRetried = false;
          try {
            const resp = await fetch('/api/chaos/simulate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                injection_type: this.chaosInjectionType,
                severity: this.chaosSeverity
              })
            });
            this.chaosResult = await resp.json();
          } catch (e) {
            console.error('Chaos simulation failed:', e);
          } finally {
            this.chaosSimulating = false;
          }
        },

        redriveDlqMessage() {
          this.dlqRetried = true;
          setTimeout(() => {
            if (this.chaosResult && this.chaosResult.deadLetterQueue) {
              this.chaosResult.deadLetterQueue.queued = false;
            }
          }, 1000);
        },

'''

if init_target not in content:
    print("❌ Could not find init_target!")
    sys.exit(1)

content = content.replace(init_target, methods + init_target, 1)
print("✅ Injected reactive methods before init()")

# 4. Inject into trainingGallerySlides
slides_target = "        trainingGallerySlides: ["
new_slides = '''        trainingGallerySlides: [
          {
            step: 7,
            title: 'Advanced A2A: A2A ⟷ MCP Bi-Directional Bridge',
            subtitle: 'Anthropic Model Context Protocol ↔ Google A2A Task Translation',
            darkImg: '/static/screenshots/dark_advanced_01_mcp_bridge.png',
            lightImg: '/static/screenshots/light_advanced_01_mcp_bridge.png',
            badge: 'MCP Protocol Bridge',
            desc: 'Cross-protocol execution converting Anthropic MCP tools/call into standard a2a.v1.ExecuteTask with sub-3µs overhead and zero metadata leakage.'
          },
          {
            step: 7,
            title: 'Advanced A2A: Multi-Agent Quorum Voting & Red-Team Debate',
            subtitle: 'Byzantine Safety Consensus & Adversarial Protocol Challenge',
            darkImg: '/static/screenshots/dark_advanced_02_quorum_debate.png',
            lightImg: '/static/screenshots/light_advanced_02_quorum_debate.png',
            badge: 'Quorum & Debate',
            desc: 'Decentralized multi-agent safety gate: FDA, EMA, and DSMB agents independently vote with Red-Team protocol challenger and Arbiter synthesis.'
          },
          {
            step: 7,
            title: 'Advanced A2A: Sequential 3-Tier 21 CFR Part 11 Multi-Sig Chain',
            subtitle: 'Cryptographic Merkle Chaining Across Multiple Human Signatories',
            darkImg: '/static/screenshots/dark_advanced_03_multisig_chain.png',
            lightImg: '/static/screenshots/light_advanced_03_multisig_chain.png',
            badge: 'Part 11 Multi-Sig',
            desc: 'Sequential cryptographic signing linking Principal Investigator, Biostatistician, and Medical Director into an immutable Merkle certificate with Cloud KMS Ed25519 signatures.'
          },
          {
            step: 7,
            title: 'Advanced A2A: In-Flight Steering & AIP-127 Checkpoint / Resumption',
            subtitle: 'Full-Duplex gRPC Steering & Long-Running Operations Snapshotting',
            darkImg: '/static/screenshots/dark_advanced_04_steering_lro.png',
            lightImg: '/static/screenshots/light_advanced_04_steering_lro.png',
            badge: 'Steering & AIP-127',
            desc: 'Dynamic mid-flight constraint injection into running streams without connection drops, paired with stateless 48-hour AIP-127 snapshot tokens.'
          },
          {
            step: 7,
            title: 'Advanced A2A: AMD SEV-SNP Enclave & Zero-Knowledge Proofs',
            subtitle: 'Hardware Memory Isolation & zk-SNARK Cohort Inclusion Verification',
            darkImg: '/static/screenshots/dark_advanced_05_enclave_zkp.png',
            lightImg: '/static/screenshots/light_advanced_05_enclave_zkp.png',
            badge: 'Enclave & ZKP',
            desc: 'Cryptographic proof of hardware enclave memory encryption (AMD SEV-SNP) and mathematical verification of clinical cohort eligibility with zero PHI transmission.'
          },
          {
            step: 7,
            title: 'Advanced A2A: Distributed W3C Tracing & Chaos Circuit Breaker',
            subtitle: 'OpenTelemetry 5-Hop Mesh Waterfall & SRE Fault Injection Simulator',
            darkImg: '/static/screenshots/dark_advanced_06_trace_chaos.png',
            lightImg: '/static/screenshots/light_advanced_06_trace_chaos.png',
            badge: 'Tracing & Chaos SRE',
            desc: 'End-to-end W3C traceparent Gantt waterfall across 5 multi-agent hops, with real-time fault injection testing circuit breaker trip (OPEN) and Dead Letter Queue re-drive.'
          },'''

if slides_target in content:
    content = content.replace(slides_target, new_slides, 1)
    print("✅ Injected 6 new Advanced Lab slides into trainingGallerySlides")
else:
    print("⚠️ Could not find slides_target, continuing...")

with open('portal/static/portal.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 Successfully updated portal.html with all Advanced A2A Lab features!")
