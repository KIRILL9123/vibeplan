"""Base adapter interface for AI coding agents."""
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


TOKEN_PATTERNS = [
    re.compile(r"(?:Tokens?|tokens?)\s*(?:used|consumed|total)?\s*[:]\s*([\d,]+)", re.IGNORECASE),
    re.compile(r"([\d,]+)\s*(?:K|k)?\s*(?:tokens?|Tokens?)", re.IGNORECASE),
    re.compile(r"(?:~?)([\d,]+)\s*(?:tokens?)\s*(?:used|consumed|total)", re.IGNORECASE),
]


@dataclass
class AdapterResult:
    success: bool = False
    exit_code: int = -1
    output: str = ""
    token_usage: Optional[int] = None
    error: str = ""


class BaseAdapter:
    name: str = ""

    @classmethod
    def check_available(cls) -> bool:
        raise NotImplementedError

    @classmethod
    def run(
        cls,
        prompt_text: str,
        context: dict,
        step: dict,
        project_dir: Path,
        agent_config: Optional[dict] = None,
    ) -> AdapterResult:
        raise NotImplementedError


class BaseCliAdapter(BaseAdapter):
    command: str = ""

    @classmethod
    def check_available(cls) -> bool:
        return bool(shutil.which(cls.command))

    @classmethod
    def run(
        cls,
        prompt_text: str,
        context: dict,
        step: dict,
        project_dir: Path,
        agent_config: Optional[dict] = None,
    ) -> AdapterResult:
        config = agent_config or {}
        pass_method = config.get("pass_method", "arg")
        extra_args = config.get("extra_args", [])

        full_prompt = cls._build_full_prompt(prompt_text, context, step)

        try:
            if pass_method == "stdin":
                result = cls._run_stdin(full_prompt, project_dir, extra_args)
            elif pass_method == "file":
                result = cls._run_file(full_prompt, project_dir, extra_args)
            else:
                result = cls._run_arg(full_prompt, project_dir, extra_args)

            token_usage = cls._parse_token_usage(result.output)
            result.token_usage = token_usage
            return result

        except FileNotFoundError:
            return AdapterResult(
                success=False,
                error=f"'{cls.command}' not found on PATH. Install {cls.name} or use manual mode.",
            )
        except Exception as e:
            return AdapterResult(success=False, error=str(e))

    @classmethod
    def _build_full_prompt(cls, prompt_text: str, context: dict, step: dict) -> str:
        budget_str = f"{step.get('tokens'):,} tokens" if step.get("tokens") else "unlimited"
        context_lines = "\n".join(f"- {k}: {v}" for k, v in context.items() if k != "original_prompt")

        return f"""You are executing Step {step['id']} — {step['name']} of a larger plan.

## Original Task
{prompt_text}

## Context
{context_lines if context_lines else "-"}

## Step Goal
{step.get('description', 'Implement this step.')}

## Token Budget
{budget_str}

## Constraints
- Focus ONLY on this step. Do not skip ahead.
- Make all changes to files as needed.
- After completing, ensure all changes are saved.
- Report back what was done."""

    @classmethod
    def _run_arg(cls, prompt: str, project_dir: Path, extra_args: List[str]) -> AdapterResult:
        cmd = [cls.command] + extra_args + [prompt]
        proc = subprocess.run(cmd, cwd=str(project_dir), capture_output=True, text=True, timeout=1800)
        return AdapterResult(
            success=proc.returncode == 0,
            exit_code=proc.returncode,
            output=proc.stdout + "\n" + proc.stderr,
        )

    @classmethod
    def _run_stdin(cls, prompt: str, project_dir: Path, extra_args: List[str]) -> AdapterResult:
        cmd = [cls.command] + extra_args
        proc = subprocess.run(cmd, cwd=str(project_dir), input=prompt, capture_output=True, text=True, timeout=1800)
        return AdapterResult(
            success=proc.returncode == 0,
            exit_code=proc.returncode,
            output=proc.stdout + "\n" + proc.stderr,
        )

    @classmethod
    def _run_file(cls, prompt: str, project_dir: Path, extra_args: List[str]) -> AdapterResult:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, prefix="vibeplan-step-") as f:
            f.write(prompt)
            prompt_path = f.name

        try:
            cmd = [cls.command] + extra_args + [prompt_path]
            proc = subprocess.run(cmd, cwd=str(project_dir), capture_output=True, text=True, timeout=1800)
            return AdapterResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode,
                output=proc.stdout + "\n" + proc.stderr,
            )
        finally:
            Path(prompt_path).unlink(missing_ok=True)

    @classmethod
    def _parse_token_usage(cls, output: str) -> Optional[int]:
        for pattern in TOKEN_PATTERNS:
            match = pattern.search(output)
            if match:
                try:
                    return int(match.group(1).replace(",", ""))
                except ValueError:
                    continue
        return None
