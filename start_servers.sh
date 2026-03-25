#!/bin/bash
# tmux is required for this to work

tmux new-session -d -s RMS 'cd backend && source .venv/bin/activate && task start'
tmux split-window -h -t RMS 'cd frontend && bun run dev'
tmux attach -t RMS