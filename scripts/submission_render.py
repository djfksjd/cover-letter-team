"""Shared submission rendering for preview and exact approved export."""

from charcount import CLAIM_RE, split_questions


def render_body(body):
    """Match DOCX soft-line joining before counting or exporting submission text."""
    clean = CLAIM_RE.sub("", body).replace("\r\n", "\n").replace("\r", "\n")
    return "\n\n".join(
        " ".join(line.strip() for line in block.splitlines() if line.strip())
        for block in clean.split("\n\n")
        if block.strip()
    )


def submission_text(source, document_type, requirements):
    sections = split_questions(source)
    if document_type != "question_answers":
        if len(sections) != 1:
            raise ValueError("Continuous document must have exactly one Q section")
        return render_body(sections[0][1]) + "\n"
    prompts = {q["id"]: q["prompt"] for q in requirements["questions"]}
    return (
        "\n\n".join(
            f"## {prompts[title.split()[0]]}\n{render_body(body)}" for title, body in sections
        )
        + "\n"
    )
