"""CLI commands for policy management and testing."""

import json
from pathlib import Path
from typing import Optional

import typer

from sboxmgr.i18n.t import t
from sboxmgr.policies import PolicyContext, policy_registry

app = typer.Typer(name="policy", help=t("Policy management commands"))


@app.command()
def list(
    group: Optional[str] = typer.Option(
        None, "--group", help=t("Filter by policy group")
    ),
    severity: Optional[str] = typer.Option(
        None, "--severity", help=t("Filter by severity level")
    ),
    enabled_only: bool = typer.Option(
        True, "--enabled/--all", help=t("Show only enabled policies")
    ),
):
    """List all registered policies, optionally filtered by group or severity."""
    policies = policy_registry.get_policies(group=group, enabled_only=enabled_only)
    if not policies:
        typer.echo(t("No policies found matching criteria"))
        return

    typer.echo(t("Registered policies:"))
    for policy in policies:
        status = "enabled" if policy.enabled else "disabled"
        typer.echo(f"  {policy.name} ({policy.group}, {status}) - {policy.description}")


@app.command()
def test(
    profile: Optional[str] = typer.Option(None, "--profile", help=t("Profile to test")),
    server: Optional[str] = typer.Option(
        None, "--server", help=t("Server to test (JSON file or inline JSON)")
    ),
    user: Optional[str] = typer.Option(None, "--user", help=t("User to test")),
    show_warnings: bool = typer.Option(
        True, "--warnings/--no-warnings", help=t("Show warning results")
    ),
    show_info: bool = typer.Option(
        False, "--info/--no-info", help=t("Show info results")
    ),
    detailed: bool = typer.Option(
        False, "--detailed", help=t("Show detailed evaluation results")
    ),
):
    """Test policies with given context using evaluate_all() for comprehensive results."""
    if not policy_registry.policies:
        typer.echo(t("No policies registered"))
        return

    # Parse server from file or inline JSON
    server_obj = None
    if server:
        try:
            if Path(server).exists():
                with open(server, "r") as f:
                    server_obj = json.load(f)
            else:
                server_obj = json.loads(server)
        except Exception as e:
            typer.echo(f"Error parsing server: {e}")
            raise typer.Exit(1)

    context = PolicyContext(
        profile=profile, server=server_obj, user=user, env={}, metadata={"test": True}
    )

    # Use evaluate_all() for comprehensive results
    try:
        evaluation_result = policy_registry.evaluate_all(context)
    except Exception as e:
        typer.echo(f"Error during policy evaluation: {e}")
        raise typer.Exit(1)

    # Display results
    typer.echo(t("Policy evaluation results:"))
    typer.echo(f"Server: {evaluation_result.server_identifier}")
    typer.echo(
        f"Overall decision: {'✅ ALLOWED' if evaluation_result.is_allowed else '❌ DENIED'}"
    )
    typer.echo(f"Reason: {evaluation_result.overall_reason}")
    typer.echo(f"Total policies evaluated: {evaluation_result.total_policies}")
    typer.echo()

    if detailed:
        typer.echo(t("Detailed results:"))
        typer.echo()

        # Show denials
        if evaluation_result.has_denials:
            typer.echo(t("❌ DENIALS:"))
            for denial in evaluation_result.denials:
                typer.echo(f"  {denial.policy_name}: {denial.reason}")
                if denial.metadata:
                    for key, value in denial.metadata.items():
                        typer.echo(f"    {key}: {value}")
            typer.echo()

        # Show warnings
        if evaluation_result.has_warnings and show_warnings:
            typer.echo(t("⚠️ WARNINGS:"))
            for warning in evaluation_result.warnings:
                typer.echo(f"  {warning.policy_name}: {warning.reason}")
                if warning.metadata:
                    for key, value in warning.metadata.items():
                        typer.echo(f"    {key}: {value}")
            typer.echo()

        # Show info results
        if evaluation_result.info_results and show_info:
            typer.echo(t("ℹ️ INFO:"))
            for info_result in evaluation_result.info_results:
                typer.echo(f"  {info_result.policy_name}: {info_result.reason}")
                if info_result.metadata:
                    for key, value in info_result.metadata.items():
                        typer.echo(f"    {key}: {value}")
            typer.echo()
    else:
        # Show summary
        if evaluation_result.has_denials:
            typer.echo(t("❌ Denials:"))
            for denial in evaluation_result.denials:
                typer.echo(f"  {denial.policy_name}: {denial.reason}")

        if evaluation_result.has_warnings and show_warnings:
            typer.echo(t("⚠️ Warnings:"))
            for warning in evaluation_result.warnings:
                typer.echo(f"  {warning.policy_name}: {warning.reason}")

        if evaluation_result.info_results and show_info:
            typer.echo(t("ℹ️ Info:"))
            for info_result in evaluation_result.info_results:
                typer.echo(f"  {info_result.policy_name}: {info_result.reason}")


@app.command()
def audit(
    profile: Optional[str] = typer.Option(
        None, "--profile", help=t("Profile to audit")
    ),
    server_file: Optional[str] = typer.Option(
        None, "--servers", help=t("File with list of servers to audit")
    ),
    output: Optional[str] = typer.Option(
        None, "--output", help=t("Output file for audit results")
    ),
    format: str = typer.Option("json", "--format", help=t("Output format: json, text")),
):
    """Audit multiple servers against all policies."""
    if not policy_registry.policies:
        typer.echo(t("No policies registered"))
        return

    # Load servers from file
    servers = []
    if server_file:
        try:
            with open(server_file, "r") as f:
                if server_file.endswith(".json"):
                    servers = json.load(f)
                else:
                    # Assume one server per line
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            try:
                                servers.append(json.loads(line))
                            except json.JSONDecodeError:
                                # Treat as simple server object
                                servers.append({"address": line, "type": "unknown"})
        except Exception as e:
            typer.echo(f"Error loading servers: {e}")
            raise typer.Exit(1)
    else:
        # Use example servers
        servers = [
            {"type": "vmess", "address": "example.com", "port": 443},
            {"type": "http", "address": "proxy.example.com", "port": 8080},
            {"type": "ss", "address": "ss.example.com", "port": 8388},
        ]

    typer.echo(t("Auditing {count} servers...").format(count=len(servers)))

    audit_results = []
    for i, server in enumerate(servers):
        context = PolicyContext(
            profile=profile,
            server=server,
            user=None,
            env={},
            metadata={"audit": True, "server_index": i},
        )

        try:
            evaluation_result = policy_registry.evaluate_all(context)
            audit_results.append(evaluation_result.to_dict())
        except Exception as e:
            audit_results.append(
                {
                    "server_identifier": context.get_server_identifier(),
                    "is_allowed": False,
                    "overall_reason": f"Evaluation error: {e}",
                    "error": str(e),
                }
            )

    # Output results
    if format == "json":
        output_data = {
            "audit_summary": {
                "total_servers": len(servers),
                "allowed_servers": sum(
                    1 for r in audit_results if r.get("is_allowed", False)
                ),
                "denied_servers": sum(
                    1 for r in audit_results if not r.get("is_allowed", True)
                ),
                "total_violations": sum(
                    len(r.get("denials", [])) for r in audit_results
                ),
                "total_warnings": sum(
                    len(r.get("warnings", [])) for r in audit_results
                ),
            },
            "results": audit_results,
        }

        if output:
            with open(output, "w") as f:
                json.dump(output_data, f, indent=2)
            typer.echo(t("Audit results saved to: {file}").format(file=output))
        else:
            typer.echo(json.dumps(output_data, indent=2))
    else:
        # Text format
        typer.echo(t("Audit Results:"))
        typer.echo("=" * 50)

        allowed_count = sum(1 for r in audit_results if r.get("is_allowed", False))
        denied_count = len(servers) - allowed_count

        typer.echo(
            t("Summary: {allowed} allowed, {denied} denied").format(
                allowed=allowed_count, denied=denied_count
            )
        )
        typer.echo()

        for result in audit_results:
            status = "✅ ALLOWED" if result.get("is_allowed", False) else "❌ DENIED"
            typer.echo(f"{result['server_identifier']}: {status}")
            typer.echo(f"  Reason: {result.get('overall_reason', 'Unknown')}")

            if result.get("denials"):
                typer.echo("  Denials:")
                for denial in result["denials"]:
                    typer.echo(f"    - {denial['policy']}: {denial['reason']}")

            if result.get("warnings"):
                typer.echo("  Warnings:")
                for warning in result["warnings"]:
                    typer.echo(f"    - {warning['policy']}: {warning['reason']}")
            typer.echo()


@app.command()
def enable(
    policy_names: str = typer.Argument(
        ..., help=t("Names of policies to enable (space-separated)")
    ),
    all: bool = typer.Option(False, "--all", help=t("Enable all policies")),
):
    """Enable one or more policies."""
    if all:
        # Enable all policies
        enabled_count = 0
        total_count = len(policy_registry.policies)

        for policy in policy_registry.policies:
            if not policy.enabled:
                policy.enabled = True
                enabled_count += 1

        if enabled_count > 0:
            typer.echo(t("Enabled {count} policies").format(count=enabled_count))
        else:
            typer.echo(t("All policies were already enabled"))

        typer.echo(t("Total policies: {total}").format(total=total_count))
        return

    # Enable specific policies
    if not policy_names:
        typer.echo(t("No policy names provided"))
        raise typer.Exit(1)

    # Split policy names by space
    names = policy_names.split()

    results = []
    for policy_name in names:
        if policy_registry.enable(policy_name):
            results.append(("✅", policy_name, "enabled"))
        else:
            results.append(("❌", policy_name, "not found"))

    # Display results
    for status, name, message in results:
        typer.echo(f"{status} {name}: {message}")

    # Exit with error if any policy was not found
    failed_count = sum(1 for status, _, _ in results if status == "❌")
    if failed_count > 0:
        typer.echo(t("Failed to enable {count} policy(ies)").format(count=failed_count))
        raise typer.Exit(1)


@app.command()
def disable(
    policy_names: str = typer.Argument(
        ..., help=t("Names of policies to disable (space-separated)")
    ),
    all: bool = typer.Option(False, "--all", help=t("Disable all policies")),
):
    """Disable one or more policies."""
    if all:
        # Disable all policies
        disabled_count = 0
        total_count = len(policy_registry.policies)

        for policy in policy_registry.policies:
            if policy.enabled:
                policy.enabled = False
                disabled_count += 1

        if disabled_count > 0:
            typer.echo(t("Disabled {count} policies").format(count=disabled_count))
        else:
            typer.echo(t("All policies were already disabled"))

        typer.echo(t("Total policies: {total}").format(total=total_count))
        return

    # Disable specific policies
    if not policy_names:
        typer.echo(t("No policy names provided"))
        raise typer.Exit(1)

    # Split policy names by space
    names = policy_names.split()

    results = []
    for policy_name in names:
        if policy_registry.disable(policy_name):
            results.append(("✅", policy_name, "disabled"))
        else:
            results.append(("❌", policy_name, "not found"))

    # Display results
    for status, name, message in results:
        typer.echo(f"{status} {name}: {message}")

    # Exit with error if any policy was not found
    failed_count = sum(1 for status, _, _ in results if status == "❌")
    if failed_count > 0:
        typer.echo(
            t("Failed to disable {count} policy(ies)").format(count=failed_count)
        )
        raise typer.Exit(1)


@app.command()
def info():
    """Show policy system information and examples."""
    typer.echo(t("Policy System Information"))
    typer.echo("=" * 40)
    typer.echo()

    typer.echo(t("Available Policy Groups:"))
    groups = {}
    for policy in policy_registry.policies:
        group = getattr(policy, "group", "default")
        if group not in groups:
            groups[group] = []
        groups[group].append(policy.name)

    for group, policies in groups.items():
        typer.echo(f"  {group}: {', '.join(policies)}")

    typer.echo()
    typer.echo(t("Security Policy Examples:"))
    typer.echo("  ProtocolPolicy: blocks http, socks5; allows vless, hysteria2")
    typer.echo("  EncryptionPolicy: requires strong encryption (tls, aes-256-gcm)")
    typer.echo("  AuthenticationPolicy: validates auth methods and password length")
    typer.echo()
    typer.echo(t("Usage Examples:"))
    typer.echo('  sboxctl policy test --server \'{"protocol": "http"}\'')
    typer.echo("  sboxctl policy test --server server.json --user admin --detailed")
    typer.echo("  sboxctl policy list --group security")
    typer.echo("  sboxctl policy enable CountryPolicy")
    typer.echo("  sboxctl policy audit --servers servers.json --output audit.json")
