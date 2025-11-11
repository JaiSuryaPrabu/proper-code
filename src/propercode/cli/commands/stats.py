# this entire code is written by propercode agent and this code is under testing !!!

"""
Stats command for displaying LLM token usage statistics.

This module implements a Typer command group that analyzes the memory store
to estimate and display token usage statistics from conversations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

app = typer.Typer(help="Display LLM token usage statistics (note: it's in testing and it's completly implemented by propercode itself)")
console = Console()


class TokenEstimator:
    """Estimate token usage from conversation content."""
    
    # Industry standard approximation: 1 token ≈ 4 characters
    # This can be refined based on actual usage patterns
    CHAR_TO_TOKEN_RATIO = 4
    
    @staticmethod
    def estimate_tokens_from_text(text: str) -> int:
        """Estimate tokens from text content."""
        if not text:
            return 0
        return max(1, len(text) // TokenEstimator.CHAR_TO_TOKEN_RATIO)
    
    @staticmethod
    def estimate_tokens_from_conversation(conversation_data: Dict[str, Any]) -> int:
        """Estimate tokens from a conversation record."""
        total_tokens = 0
        
        # Estimate from user messages
        if 'user_message' in conversation_data and conversation_data['user_message']:
            total_tokens += TokenEstimator.estimate_tokens_from_text(
                str(conversation_data['user_message'])
            )
        
        # Estimate from assistant responses
        if 'assistant_response' in conversation_data and conversation_data['assistant_response']:
            total_tokens += TokenEstimator.estimate_tokens_from_text(
                str(conversation_data['assistant_response'])
            )
        
        # Estimate from metadata
        if 'metadata' in conversation_data and conversation_data['metadata']:
            total_tokens += TokenEstimator.estimate_tokens_from_text(
                str(conversation_data['metadata'])
            )
        
        return total_tokens


def get_memory_db_path() -> Path:
    """Get the path to the memory database."""
    home_dir = Path.home()
    return home_dir / ".propercode" / "memory.db"


def analyze_conversations() -> Dict[str, Any]:
    """Analyze all conversations in the memory store."""
    db_path = get_memory_db_path()
    
    if not db_path.exists():
        return {
            "total_conversations": 0,
            "total_tokens": 0,
            "total_characters": 0,
            "conversations": []
        }
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Get all conversations
            cursor.execute("""
                SELECT id, session_id, user_message, assistant_response, 
                       created_at, updated_at, metadata
                FROM conversations
                ORDER BY created_at DESC
            """)
            
            conversations = []
            total_tokens = 0
            total_characters = 0
            
            for row in cursor.fetchall():
                conv_id, session_id, user_msg, assistant_resp, created_at, updated_at, metadata = row
                
                # Calculate token estimates
                user_tokens = TokenEstimator.estimate_tokens_from_text(user_msg or "")
                assistant_tokens = TokenEstimator.estimate_tokens_from_text(assistant_resp or "")
                metadata_tokens = TokenEstimator.estimate_tokens_from_text(metadata or "")
                
                conv_tokens = user_tokens + assistant_tokens + metadata_tokens
                conv_characters = len(user_msg or "") + len(assistant_resp or "") + len(metadata or "")
                
                conversation = {
                    "id": conv_id,
                    "session_id": session_id,
                    "user_message": user_msg,
                    "assistant_response": assistant_resp,
                    "user_tokens": user_tokens,
                    "assistant_tokens": assistant_tokens,
                    "metadata_tokens": metadata_tokens,
                    "total_tokens": conv_tokens,
                    "total_characters": conv_characters,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "metadata": metadata
                }
                
                conversations.append(conversation)
                total_tokens += conv_tokens
                total_characters += conv_characters
            
            return {
                "total_conversations": len(conversations),
                "total_tokens": total_tokens,
                "total_characters": total_characters,
                "conversations": conversations
            }
    
    except Exception as e:
        console.print(f"[red]Error analyzing conversations: {e}[/red]")
        return {
            "total_conversations": 0,
            "total_tokens": 0,
            "total_characters": 0,
            "conversations": []
        }


def analyze_by_session(conversations: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Group conversations by session and calculate statistics."""
    session_stats = {}
    
    for conv in conversations:
        session_id = conv.get("session_id", "default")
        
        if session_id not in session_stats:
            session_stats[session_id] = {
                "session_id": session_id,
                "conversation_count": 0,
                "total_tokens": 0,
                "total_characters": 0,
                "user_tokens": 0,
                "assistant_tokens": 0,
                "metadata_tokens": 0
            }
        
        session = session_stats[session_id]
        session["conversation_count"] += 1
        session["total_tokens"] += conv["total_tokens"]
        session["total_characters"] += conv["total_characters"]
        session["user_tokens"] += conv["user_tokens"]
        session["assistant_tokens"] += conv["assistant_tokens"]
        session["metadata_tokens"] += conv["metadata_tokens"]
    
    return session_stats


def get_recent_conversations(conversations: List[Dict[str, Any]], days: int = 7) -> List[Dict[str, Any]]:
    """Get conversations from the last N days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    recent = []
    for conv in conversations:
        if conv.get("created_at"):
            try:
                # Assuming created_at is in ISO format or timestamp
                if isinstance(conv["created_at"], str):
                    conv_date = datetime.fromisoformat(conv["created_at"].replace('Z', '+00:00'))
                else:
                    conv_date = datetime.fromtimestamp(conv["created_at"])
                
                if conv_date >= cutoff_date:
                    recent.append(conv)
            except (ValueError, TypeError):
                # If we can't parse the date, include it
                recent.append(conv)
    
    return recent


@app.command("overall")
def overall_stats():
    """Display overall token usage statistics."""
    console.print("[bold blue]📊 LLM Token Usage Statistics[/bold blue]\n")
    
    data = analyze_conversations()
    
    if data["total_conversations"] == 0:
        console.print("[yellow]No conversations found in memory store.[/yellow]")
        console.print("[dim]Start a conversation with 'propercode run' to generate statistics.[/dim]")
        return
    
    # Create summary panel
    summary_text = Text()
    summary_text.append(f"Total Conversations: ", style="bold")
    summary_text.append(f"{data['total_conversations']:,}\n", style="green")
    summary_text.append(f"Total Token Estimate: ", style="bold")
    summary_text.append(f"{data['total_tokens']:,}\n", style="green")
    summary_text.append(f"Total Characters: ", style="bold")
    summary_text.append(f"{data['total_characters']:,}\n", style="dim")
    summary_text.append(f"Average Tokens per Conversation: ", style="bold")
    avg_tokens = data['total_tokens'] // data['total_conversations'] if data['total_conversations'] > 0 else 0
    summary_text.append(f"{avg_tokens:,}\n", style="cyan")
    
    console.print(Panel(summary_text, title="Summary", box=box.ROUNDED))
    
    # Create detailed table
    table = Table(title="Token Usage Breakdown")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Tokens", style="green", justify="right")
    table.add_column("Percentage", style="yellow", justify="right")
    
    # Calculate breakdown from conversations
    user_total = sum(conv["user_tokens"] for conv in data["conversations"])
    assistant_total = sum(conv["assistant_tokens"] for conv in data["conversations"])
    metadata_total = sum(conv["metadata_tokens"] for conv in data["conversations"])
    
    if data["total_tokens"] > 0:
        user_pct = (user_total / data["total_tokens"]) * 100
        assistant_pct = (assistant_total / data["total_tokens"]) * 100
        metadata_pct = (metadata_total / data["total_tokens"]) * 100
    else:
        user_pct = assistant_pct = metadata_pct = 0
    
    table.add_row("User Messages", f"{user_total:,}", f"{user_pct:.1f}%")
    table.add_row("Assistant Responses", f"{assistant_total:,}", f"{assistant_pct:.1f}%")
    table.add_row("Metadata", f"{metadata_total:,}", f"{metadata_pct:.1f}%")
    
    console.print("\n")
    console.print(table)


@app.command("by-session")
def session_stats():
    """Display token usage statistics by session."""
    console.print("[bold blue]🔗 Session-based Token Usage[/bold blue]\n")
    
    data = analyze_conversations()
    
    if data["total_conversations"] == 0:
        console.print("[yellow]No conversations found in memory store.[/yellow]")
        return
    
    session_stats = analyze_by_session(data["conversations"])
    
    if not session_stats:
        console.print("[yellow]No session data available.[/yellow]")
        return
    
    # Create table
    table = Table(title="Token Usage by Session")
    table.add_column("Session ID", style="cyan")
    table.add_column("Conversations", style="green", justify="right")
    table.add_column("Total Tokens", style="yellow", justify="right")
    table.add_column("User Tokens", style="blue", justify="right")
    table.add_column("Assistant Tokens", style="magenta", justify="right")
    table.add_column("Avg Tokens/Conv", style="dim", justify="right")
    
    # Sort sessions by total tokens (descending)
    sorted_sessions = sorted(
        session_stats.values(), 
        key=lambda x: x["total_tokens"], 
        reverse=True
    )
    
    for session in sorted_sessions:
        avg_tokens = session["total_tokens"] // session["conversation_count"] if session["conversation_count"] > 0 else 0
        
        table.add_row(
            session["session_id"][:20] + "..." if len(session["session_id"]) > 20 else session["session_id"],
            f"{session['conversation_count']:,}",
            f"{session['total_tokens']:,}",
            f"{session['user_tokens']:,}",
            f"{session['assistant_tokens']:,}",
            f"{avg_tokens:,}"
        )
    
    console.print(table)


@app.command("recent")
def recent_stats(
    days: Optional[int] = typer.Option(7, "--days", "-d", help="Number of days to look back")
):
    """Display recent token usage statistics."""
    console.print(f"[bold blue]📅 Recent Token Usage (Last {days} Days)[/bold blue]\n")
    
    data = analyze_conversations()
    
    if data["total_conversations"] == 0:
        console.print("[yellow]No conversations found in memory store.[/yellow]")
        return
    
    recent_conversations = get_recent_conversations(data["conversations"], days or 0)
    
    if not recent_conversations:
        console.print(f"[yellow]No conversations found in the last {days} days.[/yellow]")
        return
    
    # Calculate recent statistics
    recent_total_tokens = sum(conv["total_tokens"] for conv in recent_conversations)
    recent_user_tokens = sum(conv["user_tokens"] for conv in recent_conversations)
    recent_assistant_tokens = sum(conv["assistant_tokens"] for conv in recent_conversations)
    recent_characters = sum(conv["total_characters"] for conv in recent_conversations)
    
    # Create summary
    summary_text = Text()
    summary_text.append(f"Recent Conversations: ", style="bold")
    summary_text.append(f"{len(recent_conversations):,}\n", style="green")
    summary_text.append(f"Recent Token Estimate: ", style="bold")
    summary_text.append(f"{recent_total_tokens:,}\n", style="green")
    summary_text.append(f"Recent Characters: ", style="bold")
    summary_text.append(f"{recent_characters:,}\n", style="dim")
    summary_text.append(f"Daily Average: ", style="bold")
    if days is not None:
        daily_avg = recent_total_tokens // days if days > 0 else 0
        summary_text.append(f"{daily_avg:,} tokens/day\n", style="cyan")
    
    console.print(Panel(summary_text, title="Recent Activity Summary", box=box.ROUNDED))
    
    # Show top recent conversations
    if recent_conversations:
        console.print("\n[bold]Top Recent Conversations by Token Usage:[/bold]")
        
        table = Table()
        table.add_column("Session", style="cyan")
        table.add_column("Tokens", style="green", justify="right")
        table.add_column("User", style="blue", justify="right")
        table.add_column("Assistant", style="magenta", justify="right")
        table.add_column("Date", style="dim")
        
        # Sort by token usage (descending) and take top 10
        top_conversations = sorted(
            recent_conversations, 
            key=lambda x: x["total_tokens"], 
            reverse=True
        )[:10]
        
        for conv in top_conversations:
            session_short = conv["session_id"][:15] + "..." if len(conv["session_id"]) > 15 else conv["session_id"]
            date_str = conv.get("created_at", "Unknown")[:10] if conv.get("created_at") else "Unknown"
            
            table.add_row(
                session_short,
                f"{conv['total_tokens']:,}",
                f"{conv['user_tokens']:,}",
                f"{conv['assistant_tokens']:,}",
                date_str
            )
        
        console.print(table)


if __name__ == "__main__":
    app()