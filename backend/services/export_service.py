"""
Export service for generating deliverable files.

Handles TXT, Markdown, and DOCX export generation from database posts.
"""

import json
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
    include_research: bool = False,
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
        include_research: Whether to include research results appendix
        db: Database session (required if include_audit_log or include_research is True)

    Returns:
        Tuple of (absolute file path, file size in bytes)
    """
    # Ensure output directory exists
    output_dir = Path("data/outputs")
    full_path = output_dir / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "docx":
        return await _generate_docx(
            posts, client, project, full_path, include_audit_log, include_research, db
        )
    elif format == "md" or format == "markdown":
        return await _generate_markdown(
            posts, client, project, full_path, include_audit_log, include_research, db
        )
    else:
        return await _generate_txt(
            posts, client, project, full_path, include_audit_log, include_research, db
        )


async def _generate_txt(
    posts: List[Post],
    client: Client,
    project: Project,
    output_path: Path,
    include_audit_log: bool,
    include_research: bool,
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

    # Research results (if requested)
    if include_research and db:
        research_sections = _generate_research_section(project.id, db)
        if research_sections:
            lines.append("")
            lines.append("=" * 60)
            lines.append("RESEARCH RESULTS")
            lines.append("=" * 60)
            lines.append("")

            for tool_name, section_lines in research_sections.items():
                lines.extend(section_lines)
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
    include_research: bool,
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

    # Research results (if requested)
    if include_research and db:
        research_sections = _generate_research_section(project.id, db)
        if research_sections:
            lines.append("---")
            lines.append("")
            lines.append("## Research Results")
            lines.append("")

            for tool_name, section_lines in research_sections.items():
                lines.extend(section_lines)
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
    include_research: bool,
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

    # Research results (if requested)
    if include_research and db:
        research_sections = _generate_research_section(project.id, db)
        if research_sections:
            doc.add_page_break()
            doc.add_heading("Research Results", level=1)

            for tool_name, section_lines in research_sections.items():
                for line in section_lines:
                    if line.startswith("# "):
                        doc.add_heading(line[2:], level=2)
                    elif line.startswith("## "):
                        doc.add_heading(line[3:], level=3)
                    elif line.startswith("|"):
                        # Table row - skip for now (complex DOCX table formatting)
                        doc.add_paragraph(line)
                    elif line:
                        doc.add_paragraph(line)

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


def _generate_research_section(project_id: str, db: Session) -> dict:
    """
    Generate research results section for deliverables.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Dict mapping tool_name -> list of formatted lines
    """
    from backend.services import crud

    results = crud.get_research_results_by_project(db, project_id, status="completed")
    if not results:
        return {}

    research_sections = {}

    for result in results:
        lines = []
        lines.append(f"# {result.tool_label or result.tool_name}")
        lines.append("")

        # Metadata
        if result.created_at:
            lines.append(f"**Executed:** {result.created_at.strftime('%B %d, %Y at %H:%M')}")
        if result.tool_price:
            lines.append(f"**Cost:** ${result.tool_price:.2f}")
        lines.append("")

        # Format tool-specific data
        if result.data:
            lines.append("## Executive Summary")
            lines.append("")

            if result.tool_name == "voice_analysis":
                lines.extend(_format_voice_analysis(result.data))
            elif result.tool_name == "brand_archetype":
                lines.extend(_format_brand_archetype(result.data))
            elif result.tool_name == "seo_keyword_research":
                lines.extend(_format_seo_keywords(result.data))
            elif result.tool_name == "competitive_analysis":
                lines.extend(_format_competitive_analysis(result.data))
            elif result.tool_name == "content_gap_analysis":
                lines.extend(_format_content_gap(result.data))
            elif result.tool_name == "market_trends_research":
                lines.extend(_format_market_trends(result.data))
            else:
                # Generic fallback for other tools
                lines.extend(_format_generic_research(result.data))

            lines.append("")

        # Full report from output files
        if result.outputs:
            full_report_lines = _read_output_files(result.outputs)
            if full_report_lines:
                lines.append("---")
                lines.append("")
                lines.append("## Full Report")
                lines.append("")
                lines.extend(full_report_lines)
                lines.append("")

        research_sections[result.tool_name] = lines

    return research_sections


def _read_output_files(outputs: dict) -> List[str]:
    """
    Read and format output files from research tools.

    Args:
        outputs: Dict mapping format -> file path
                 Example: {"markdown": "path/to/report.md"}

    Returns:
        List of formatted lines to include in deliverable
    """
    lines: List[str] = []

    if not outputs or not isinstance(outputs, dict):
        return lines

    # Prefer markdown format for readability
    if "markdown" in outputs and outputs["markdown"]:
        markdown_path = Path(outputs["markdown"])
        try:
            if markdown_path.exists() and markdown_path.is_file():
                content = markdown_path.read_text(encoding="utf-8")
                lines.append(content)
                logger.info(f"Included markdown output: {markdown_path}")
            else:
                logger.warning(f"Markdown output file not found: {markdown_path}")
                lines.append("*Full markdown report unavailable (file not found)*")
        except Exception as e:
            logger.error(f"Error reading markdown output {markdown_path}: {e}")
            lines.append(f"*Full report unavailable (error: {e})*")

    # Fallback to JSON if markdown not available
    elif "json" in outputs and outputs["json"]:
        json_path = Path(outputs["json"])
        try:
            if json_path.exists() and json_path.is_file():
                with json_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                lines.append("```json")
                lines.append(json.dumps(data, indent=2, ensure_ascii=False))
                lines.append("```")
                logger.info(f"Included JSON output: {json_path}")
            else:
                logger.warning(f"JSON output file not found: {json_path}")
                lines.append("*Full JSON report unavailable (file not found)*")
        except Exception as e:
            logger.error(f"Error reading JSON output {json_path}: {e}")
            lines.append(f"*Full report unavailable (error: {e})*")
    else:
        logger.info("No markdown or JSON output available")
        lines.append("*Full report not available for this tool*")

    return lines


def _format_voice_analysis(data: dict) -> List[str]:
    """Format voice analysis results."""
    lines = []
    if "tone" in data:
        lines.append(f"**Tone:** {data['tone']}")
    if "readability_score" in data:
        lines.append(f"**Readability Score:** {data['readability_score']}")
    if "recommendations" in data and isinstance(data["recommendations"], list):
        lines.append("")
        lines.append("**Recommendations:**")
        for rec in data["recommendations"]:
            lines.append(f"- {rec}")
    return lines


def _format_brand_archetype(data: dict) -> List[str]:
    """Format brand archetype results."""
    lines = []
    if "primary_archetype" in data:
        lines.append(f"**Primary Archetype:** {data['primary_archetype']}")
    if "secondary_archetype" in data:
        lines.append(f"**Secondary Archetype:** {data['secondary_archetype']}")
    if "content_themes" in data and isinstance(data["content_themes"], list):
        lines.append("")
        lines.append("**Content Themes:**")
        for theme in data["content_themes"]:
            lines.append(f"- {theme}")
    return lines


def _format_seo_keywords(data: dict) -> List[str]:
    """Format SEO keyword results."""
    lines = []
    if "primary_keywords" in data and isinstance(data["primary_keywords"], list):
        lines.append("**Primary Keywords:**")
        lines.append("")
        lines.append("| Keyword | Volume | Difficulty |")
        lines.append("|---------|--------|------------|")
        for kw in data["primary_keywords"][:10]:  # Limit to top 10
            keyword = kw.get("keyword", "N/A")
            volume = kw.get("volume", 0)
            difficulty = kw.get("difficulty", "N/A")
            lines.append(f"| {keyword} | {volume:,} | {difficulty} |")
    return lines


def _format_competitive_analysis(data: dict) -> List[str]:
    """Format competitive analysis results."""
    lines = []
    if "competitors" in data and isinstance(data["competitors"], list):
        lines.append("**Key Competitors:**")
        lines.append("")
        for comp in data["competitors"][:5]:  # Top 5
            name = comp.get("name", "Unknown")
            strength = comp.get("strength", "N/A")
            lines.append(f"- **{name}** (Strength: {strength})")
            if "key_differentiator" in comp:
                lines.append(f"  - {comp['key_differentiator']}")
    return lines


def _format_content_gap(data: dict) -> List[str]:
    """Format content gap analysis results."""
    lines = []

    # Executive summary
    if "executive_summary" in data:
        lines.append(data["executive_summary"])
        lines.append("")

    # Total gaps and opportunity
    if "total_gaps_identified" in data:
        lines.append(f"**Total Gaps Identified:** {data['total_gaps_identified']}")
    if "estimated_opportunity" in data:
        lines.append(f"**Estimated Opportunity:** {data['estimated_opportunity']}")
        lines.append("")

    # Generic gaps field (for simple data structures)
    gaps = data.get("gaps", [])
    if gaps:
        lines.append("**Content Gaps Identified:**")
        lines.append("")
        for gap in gaps:
            if isinstance(gap, dict):
                # Handle dict with topic/priority or similar fields
                topic = gap.get("topic", gap.get("gap_title", "Unknown"))
                priority = gap.get("priority", gap.get("gap_priority", ""))
                if priority:
                    lines.append(f"- **{topic}** (Priority: {priority})")
                else:
                    lines.append(f"- **{topic}**")
            else:
                # Handle simple string gaps
                lines.append(f"- {gap}")
        lines.append("")

    # Critical gaps
    critical_gaps = data.get("critical_gaps", [])
    if critical_gaps:
        lines.append("### Critical Priority Gaps")
        lines.append("")
        for gap in critical_gaps[:5]:  # Limit to 5 critical gaps
            if isinstance(gap, dict):
                title = gap.get("gap_title", "Unknown")
                gap_type = gap.get("gap_type", "N/A")
                description = gap.get("description", "")
                impact = gap.get("business_impact", "")
                lines.append(f"**{title}** ({gap_type})")
                if description:
                    lines.append(f"  - {description}")
                if impact:
                    lines.append(f"  - Impact: {impact}")
                lines.append("")

    # High priority gaps
    high_gaps = data.get("high_priority_gaps", [])
    if high_gaps:
        lines.append("### High Priority Gaps")
        lines.append("")
        for gap in high_gaps[:3]:
            if isinstance(gap, dict):
                title = gap.get("gap_title", "Unknown")
                description = gap.get("description", "")
                lines.append(f"- **{title}**: {description}")
        lines.append("")

    # Immediate actions
    actions = data.get("immediate_actions", [])
    if actions:
        lines.append("### Immediate Actions")
        lines.append("")
        for action in actions[:5]:
            lines.append(f"- {action}")
        lines.append("")

    return lines


def _format_market_trends(data: dict) -> List[str]:
    """Format market trends results."""
    lines = []
    if "trends" in data and isinstance(data["trends"], list):
        lines.append("**Top Market Trends:**")
        lines.append("")
        for trend in data["trends"][:8]:
            if isinstance(trend, dict):
                title = trend.get("title", "Unknown")
                impact = trend.get("impact", "N/A")
                lines.append(f"- **{title}** (Impact: {impact})")
            else:
                lines.append(f"- {trend}")
    return lines


def _format_generic_research(data: dict) -> List[str]:
    """Generic fallback formatter for research data."""
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"**{key.replace('_', ' ').title()}:**")
            for item in value[:10]:  # Limit to 10 items
                lines.append(f"- {item}")
            lines.append("")
        elif isinstance(value, dict):
            lines.append(f"**{key.replace('_', ' ').title()}:**")
            for subkey, subval in value.items():
                lines.append(f"- {subkey}: {subval}")
            lines.append("")
        else:
            lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
    return lines
