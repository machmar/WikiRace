# Refuse to open or touch anything on GitHub under the owner's name.
#
# Issues, pull requests and comments carry whoever the gh token belongs to, and
# work Claude does should say so. The machine account machmar-claude has its own
# gh config directory; this blocks the write commands unless that is what's
# being used. Reading, cloning, watching CI and the like are untouched.
#
# Runs as a PreToolUse hook on Bash and PowerShell, with the tool call on stdin.

$raw = [Console]::In.ReadToEnd()
try { $call = $raw | ConvertFrom-Json } catch { exit 0 }

$cmd = $call.tool_input.command
if (-not $cmd) { exit 0 }

# The commands that stamp a name on something everyone can see.
$writes = 'gh\s+(pr|issue)\s+(create|comment|edit|close|reopen|ready|review|lock|unlock|transfer|delete|pin|unpin)'
if ($cmd -notmatch $writes) { exit 0 }

# Either the command names the machine account's config itself, or the session
# is already running with it.
if ($cmd -match 'gh-claude') { exit 0 }
if ($env:GH_CONFIG_DIR -and $env:GH_CONFIG_DIR -match 'gh-claude') { exit 0 }

$reason = @'
Blocked: that would file as the repository owner.

Issues and pull requests Claude opens go under the machine account
machmar-claude, so the history says who wrote what. Run it with that account's
gh config instead:

  $env:GH_CONFIG_DIR = "$env:USERPROFILE\.config\gh-claude"

and assign the work to machmar-claude. See .claude/notes/workflows.md.
'@

$out = @{
  hookSpecificOutput = @{
    hookEventName            = 'PreToolUse'
    permissionDecision       = 'deny'
    permissionDecisionReason = $reason
  }
}
$out | ConvertTo-Json -Depth 5 -Compress
exit 0
