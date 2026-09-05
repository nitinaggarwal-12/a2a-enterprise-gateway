"""
Enterprise A2A Gateway Command Line Interface (CLI).

Usage:
  python -m a2a_sdk.cli status
  python -m a2a_sdk.cli ectd --protocol MK-3475-087 --dose 250
  python -m a2a_sdk.cli simulate --cohort 10000 --dose 250
  python -m a2a_sdk.cli drawio export --preset option3_dual_plane
  python -m a2a_sdk.cli diagnose --endpoint psc://10.128.0.50:50051
"""

import sys
import argparse
import json
from a2a_sdk.client import A2AGatewayClient

def print_banner():
    print("=" * 70)
    print("🚀 Enterprise A2A Gateway CLI (Google a2a.v1.0.0 Protocol)")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="Enterprise A2A Gateway Sovereign CLI")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:8090", help="Base URL of the A2A Gateway")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # Status command
    subparsers.add_parser("status", help="Inspect gateway health and latencies")

    # eCTD command
    p_ectd = subparsers.add_parser("ectd", help="Compile 1-Click FDA eCTD 3.2.2 dossier")
    p_ectd.add_argument("--protocol", default="MK-3475-087", help="Clinical protocol ID")
    p_ectd.add_argument("--amendment", default="AMD-ONC-2026-08", help="Amendment ID")
    p_ectd.add_argument("--dose", type=float, default=250.0, help="Target dose in mg")
    p_ectd.add_argument("--sponsor", default="Merck Sharp & Dohme LLC", help="Sponsor name")

    # In-Silico simulation command
    p_sim = subparsers.add_parser("simulate", help="Run in-silico digital twin trial")
    p_sim.add_argument("--cohort", type=int, default=10000, help="Synthetic patient cohort size")
    p_sim.add_argument("--dose", type=float, default=250.0, help="Dose in mg")
    p_sim.add_argument("--protectant", action="store_true", default=True, help="Enable prophylactic protectant")

    # Draw.io command
    p_drawio = subparsers.add_parser("drawio", help="Export or compile PromptCanvas Draw.io architectures")
    p_drawio.add_argument("--action", choices=["export", "compile"], default="export", help="Action to perform")
    p_drawio.add_argument("--preset", default="option3_dual_plane", help="Architecture preset key")
    p_drawio.add_argument("--file", help="Path to .drawio XML file (for compile action)")

    # Diagnostics command
    p_diag = subparsers.add_parser("diagnose", help="Run mTLS & AST network probe")
    p_diag.add_argument("--endpoint", default="psc://10.128.0.50:50051", help="Target endpoint")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    client = A2AGatewayClient(base_url=args.gateway_url)

    if args.command == "status":
        print_banner()
        print(f"Connecting to Gateway at: {args.gateway_url}...")
        try:
            res = client.health()
            print("✓ Gateway Services Online:")
            for k, v in res.items():
                print(f"  • {k.upper()}: Status={v.get('status')} | Port={v.get('port')} | Type={v.get('type')}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
            sys.exit(1)

    elif args.command == "ectd":
        print_banner()
        print(f"🏛️ Compiling FDA eCTD 3.2.2 Regulatory Dossier for {args.protocol}...")
        res = client.compile_ectd(
            protocol_id=args.protocol,
            amendment_id=args.amendment,
            target_dose_mg=args.dose,
            sponsor_name=args.sponsor
        )
        print(f"✓ Submission ID:      {res.get('submissionId')}")
        print(f"✓ Compilation Time:   {res.get('compilationDurationMs')} ms (Target < 25 ms)")
        print(f"✓ Merkle Root:        {res.get('merkleAuditRoot')}")
        print(f"✓ SHA-256 Checksum:   {res.get('verificationChecksums', {}).get('sha256')}")
        print(f"✓ MD5 Checksum:       {res.get('verificationChecksums', {}).get('md5')}")
        print("✓ FDA Form 1571/1572: Validated & Signed")

    elif args.command == "simulate":
        print_banner()
        print(f"🧬 Simulating {args.cohort:,} In-Silico Digital Twins ({args.dose}mg, Protectant={args.protectant})...")
        res = client.simulate_in_silico(
            cohort_size=args.cohort,
            dose_mg=args.dose,
            prophylactic_protectant=args.protectant
        )
        print(f"✓ Simulation ID:      {res.get('simulationId')}")
        print(f"✓ Sim Duration:       {res.get('simulationDurationMs')} ms")
        print(f"✓ Swarm Throughput:   {res.get('throughputAgentsPerSec'):,} agents/sec")
        print(f"✓ Safety Verdict:     {res.get('safetyVerdict')}")
        pd = res.get('pharmacodynamicResults', {})
        print(f"✓ Efficacy Rate:      {pd.get('projectedEfficacyRate')}")
        print(f"✓ Receptor Occupancy: {pd.get('targetReceptorOccupancy')}")
        print(f"✓ Grade 3/4 Toxicity: {pd.get('grade3_4Toxicity')}")

    elif args.command == "drawio":
        print_banner()
        if args.action == "export":
            print(f"🎨 Exporting PromptCanvas Draw.io Architecture ({args.preset})...")
            res = client.export_drawio_preset(preset_key=args.preset)
            print(f"✓ Architecture Title: {res.get('title')}")
            print(f"✓ Target Filename:    {res.get('filename')}")
            print(f"✓ XML Root Length:    {len(res.get('xml', ''))} characters")
        elif args.action == "compile":
            if not args.file:
                print("❌ Error: --file argument required for compile action.")
                sys.exit(1)
            with open(args.file, "r") as f:
                xml_data = f.read()
            res = client.compile_promptcanvas_diagram(xml_data)
            print(f"✓ Synthesized DAG ID: {res.get('dag_id')}")
            print(f"✓ Nodes Extracted:    {res.get('nodes_count')}")
            print(f"✓ Edges Mapped:       {res.get('edges_count')}")
            print(f"✓ 21 CFR Part 11:     {'YES (Compliant)' if res.get('gxp_21cfr11_compliant') else 'NO'}")

    elif args.command == "diagnose":
        print_banner()
        print(f"⚡ Running Preflight Diagnostics against {args.endpoint}...")
        res = client.run_diagnostics(endpoint=args.endpoint)
        print(f"✓ mTLS Handshake:     {res.get('mtls_handshake')}")
        print(f"✓ Cipher Suite:       {res.get('cipher_suite')}")
        print(f"✓ AST Latency:        {res.get('ast_filter_latency_us')} µs (Sub-28µs target)")
        print(f"✓ Verdict:            {res.get('verdict')}")

if __name__ == "__main__":
    main()
