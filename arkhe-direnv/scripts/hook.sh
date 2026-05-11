#!/bin/bash

# arkhe-direnv hook bash
# To use this hook, add the following to your .bashrc:
# eval "$(arkhe-direnv hook bash)"

arkhe_direnv_hook() {
    local previous_exit_status=$?
    trap -- '' SIGINT
    eval "$("/usr/local/bin/arkhe-direnv" export)"
    trap - SIGINT
    return $previous_exit_status
}

if [[ ";${PROMPT_COMMAND:-};" != *";arkhe_direnv_hook;"* ]]; then
    PROMPT_COMMAND="arkhe_direnv_hook${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
fi
