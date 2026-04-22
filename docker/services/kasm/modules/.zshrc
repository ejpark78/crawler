export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="robbyrussell"

zstyle ':omz:update' mode disabled  # disable automatic updates

HYPHEN_INSENSITIVE="true"
DISABLE_AUTO_TITLE="true"
ENABLE_CORRECTION="true"
DISABLE_UNTRACKED_FILES_DIRTY="true"

plugins=(
  git 
  docker 
  helm 
  fzf 
  zsh-autosuggestions 
  zsh-syntax-highlighting
  git-prompt
  sudo 
  web-search
)

source $ZSH/oh-my-zsh.sh

# User configuration
export LANG=en_US.UTF-8

export EDITOR='vim'

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# bun completions
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# eza aliases
if command -v eza >/dev/null 2>&1; then
  alias ls='eza --icons --group-directories-first'
  alias ll='eza -lh --icons --group-directories-first'
  alias la='eza -a --icons --group-directories-first'
  alias lt='eza --tree --icons'
  alias lla='eza -lah --icons --group-directories-first'
fi

[ -f "$HOME/.fzf.zsh" ] && source ~/.fzf.zsh

alias docker="sudo docker"
alias dc='docker compose'

alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgd='kubectl get deploy'

# Fcitx5 한글 입력 설정
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
export DefaultIMModule=fcitx

# opencode & claude
export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:/usr/local/bin/opencode:/usr/local/bin/claude:/usr/local/share/playwright:$PATH
