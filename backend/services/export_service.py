"""
Export service for generating deliverable files.

Handles TXT, Markdown, and DOCX export generation from database posts.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.models.client import Client
from backend.models.post import Post
from backend.models.project import Project
from backend.utils.logger import logger


async def generate_export_file(
    posts: List[Post],
    client: Client,
    project: Project,
    format: str,
    relative_path: str,
    include_audit_log: bool = False,
    db: Optional[Session] = None,
) -> Tuple[Path, int]:
    """
    Generate export file in specified format.

    Args:
        posts: List of Post database models
        client: Client database model
        project: Project database model
        format: Export format ('txt', 'md', or 'docx')
        relative_path: Relative path for the output file (from data/outputs/)
        include_audit_log: Whether to include audit log in export
        db: Database session (required if include_audit_log is True)

    Returns:
        Tuple of (absolute file path, file size in bytes)
    """
    # Ensure output directory exists
    output_dir = Path("data/outputs")
    full_path = output_dir / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "docx":
        return await _generate_docx(posts, client, project, full_path, include_audit_log, db)
    elif format == "md" or format == "markdown":
        return await _generate_markdown(posts, client, project, full_path, include_audit_log, db)
    else:
        return await _generate_txt(posts, client, project, full_path, include_audit_log, db)


async def _generate_txt(
    posts: List[Post],
    client: Client,
    project: Project,
    output_path: Path,
    include_audit_log: bool,
    db: Optional[Session],
) -> Tuple[Path, int]:
    """Generate TXT deliverable file."""
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("30-DAY CONTENT JUMPSTART DELIVERABLE")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Client: {client.name}")
    lines.append(f"Project: {project.name}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Total Posts: {len(posts)}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    # Posts
    for i, post in enumerate(posts, 1):
        lines.append(f"POST #{i}")
        lines.append("-" * 40)
        if post.template_name:
            lines.append(f"Template: {post.template_name}")
        if post.target_platform:
            lines.append(f"Platform: {post.target_platform}")
        lines.append(f"Word Count: {post.word_count or 'N/A'}")
        lines.append(f"Has CTA: {'Yes' if post.has_cta else 'No'}")
        if post.readability_score:
            lines.append(f"Readability: {post.readability_score:.1f}")
        lines.append("")
        lines.append(post.content)
        lines.append("")
        lines.append("=" * 60)
        lines.append("")

    # Audit log (if requested)
    if include_audit_log and db:
        audit_section = _generate_audit_section(project.id, db)
        if audit_section:
            lines.append("")
            lines.append("AUDIT LOG")
            lines.append("-" * 40)
            lines.extend(audit_section)

    # Write file
    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")

    file_size = output_path.stat().st_size
    logger.info(f"Generated TXT deliverable: {output_path} ({file_size} bytes)")

    return output_path, file_size


async def _generate_markdown(
    posts: List[Post],
    client: Client,
    project: Project,
    output_path: Path,
    include_audit_log: bool,
    db: Optional[Session],
) -> Tuple[Path, int]:
    """Generate Markdown deliverable file with frontmatter."""
    lines = []

    # YAML frontmatter
    lines.append("---")
    lines.append("title: 30-Day Content Jumpstart Deliverable")
    lines.append(f"client: {client.name}")
    lines.append(f"project: {project.name}")
    lines.append(f'generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f"total_posts: {len(posts)}")
    lines.append("format: markdown")
    lines.append("---")
    lines.append("")

    # Header
    lines.append("# 30-Day Content Jumpstart Deliverable")
    lines.append("")
    lines.append(f"**Client:** {client.name}")
    lines.append(f"**Project:** {project.name}")
    lines.append(f'**Generated:** {datetime.now().strftime("%B %d, %Y at %H:%M")}')
    lines.append(f"**Total Posts:** {len(posts)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")
    for i, post in enumerate(posts, 1):
        template_name = post.template_name or "Custom"
        platform = f" ({post.target_platform})" if post.target_platform else ""
        lines.append(f"{i}. [Post {i}: {template_name}{platform}](#post-{i})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Posts section
    lines.append("## Your Posts")
    lines.append("")

    for i, post in enumerate(posts, 1):
        # Post header with anchor
        template_name = post.template_name or "Custom"
        lines.append(f"### Post {i}: {template_name} {{#post-{i}}}")
        lines.append("")

        # Metadata table
        lines.append("| Property | Value |")
        lines.append("|----------|-------|")
        if post.target_platform:
            lines.append(f"| **Platform** | {post.target_platform} |")
        lines.append(f'| **Word Count** | {post.word_count or "N/A"} |')
        lines.append(f'| **Has CTA** | {"✅ Yes" if post.has_cta else "❌ No"} |')
        if post.readability_score:
            lines.append(f"| **Readability Score** | {post.readability_score:.1f} |")
        lines.append("")

        # Post content in blockquote for easy copying
        lines.append("#### Content")
        lines.append("")
        # Add content as blockquote (simpler approach - just prepend > to content)
        for line in post.content.split("\n"):
            lines.append(f"> {line}")
        lines.append("")

        # Separator
        lines.append("---")
        lines.append("")

    # Audit log (if requested)
    if include_audit_log and db:
        audit_section = _generate_audit_section(project.id, db)
        if audit_section:
            lines.append("## Audit Log")
            lines.append("")
            lines.append("```")
            lines.extend(audit_section)
            lines.append("```")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated by 30-Day Content Jumpstart*")
    lines.append("")

    # Write file
    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")

    file_size = output_path.stat().st_size
    logger.info(f"Generated Markdown deliverable: {output_path} ({file_size} bytes)")

    return output_path, file_size


async def _generate_docx(
    posts: List[Post],
    client: Client,
    project: Project,
    output_path: Path,
    include_audit_log: bool,
    db: Optional[Session],
) -> Tuple[Path, int]:
    """Generate DOCX deliverable file."""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        logger.warning("python-docx not installed, falling back to TXT")
        # Fall back to TXT if docx not available
        txt_path = output_path.with_suffix(".txt")
        return await _generate_txt(posts, client, project, txt_path, include_audit_log, db)

    # Create document
    doc = Document()

    # Brand color
    brand_color = RGBColor(41, 128, 185)

    # Title page
    title = doc.add_paragraph()
    title_run = title.add_run("30-Day Content Jumpstart")
    title_run.font.name = "Calibri"
    title_run.font.size = Pt(28)
    title_run.font.bold = True
    title_run.font.color.rgb = brand_color
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Client name
    client_para = doc.add_paragraph()
    client_run = client_para.add_run(client.name)
    client_run.font.name = "Calibri"
    client_run.font.size = Pt(22)
    client_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Date
    date_para = doc.add_paragraph()
    date_run = date_para.add_run(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    date_run.font.name = "Calibri"
    date_run.font.size = Pt(12)
    date_run.font.italic = True
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    # Introduction
    doc.add_heading("About This Content Package", level=1)
    doc.add_paragraph(
        f"This content package has been custom-generated for {client.name}. "
        f"All {len(posts)} posts are tailored to your brand voice, target audience, and business goals."
    )

    doc.add_paragraph()

    # Client info table
    table = doc.add_table(rows=3, cols=2)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "Client"
    table.rows[0].cells[1].text = client.name
    table.rows[1].cells[0].text = "Project"
    table.rows[1].cells[1].text = project.name
    table.rows[2].cells[0].text = "Total Posts"
    table.rows[2].cells[1].text = str(len(posts))

    doc.add_page_break()

    # Posts section
    doc.add_heading("Your Posts", level=1)

    for i, post in enumerate(posts, 1):
        # Post header
        doc.add_heading(f"Post {i}: {post.template_name or 'Custom'}", level=2)

        # Post content
        content_para = doc.add_paragraph(post.content)
        content_para.paragraph_format.space_after = Pt(12)

        # Metadata
        metadata_parts = [f"Words: {post.word_count or 'N/A'}"]
        if post.target_platform:
            metadata_parts.insert(0, f"Platform: {post.target_platform}")
        metadata_parts.append(f"Has CTA: {'Yes' if post.has_cta else 'No'}")
        if post.readability_score:
            metadata_parts.append(f"Readability: {post.readability_score:.1f}")

        metadata_para = doc.add_paragraph(" | ".join(metadata_parts))
        metadata_para.runs[0].font.size = Pt(9)
        metadata_para.runs[0].font.italic = True
        metadata_para.runs[0].font.color.rgb = RGBColor(127, 140, 141)

        # Separator
        doc.add_paragraph("_" * 80)

        # Page break every 5 posts
        if i % 5 == 0 and i < len(posts):
            doc.add_page_break()

    # Audit log (if requested)
    if include_audit_log and db:
        audit_section = _generate_audit_section(project.id, db)
        if audit_section:
            doc.add_page_break()
            doc.add_heading("Audit Log", level=1)
            for line in audit_section:
                doc.add_paragraph(line)

    # Save document
    doc.save(str(output_path))

    file_size = output_path.stat().st_size
    logger.info(f"Generated DOCX deliverable: {output_path} ({file_size} bytes)")

    return output_path, file_size


def _generate_audit_section(project_id: str, db: Session) -> List[str]:
    """Generate audit log section for a project."""
    lines = []

    try:
        from backend.models import AuditLog

        # Query audit logs for this project
        audit_logs = (
            db.query(AuditLog)
            .filter(
                (AuditLog.target_id == project_id)
                | (AuditLog.metadata.contains({"project_id": project_id}))
            )
            .order_by(AuditLog.timestamp.asc())
            .limit(100)
            .all()
        )

        if not audit_logs:
            return []

        for log in audit_logs:
            timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "N/A"
            lines.append(f"[{timestamp}] {log.actor}: {log.action} on {log.target_type}")

    except Exception as e:
        logger.warning(f"Could not generate audit section: {e}")
        return []

    return lines
