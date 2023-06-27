#!/usr/bin/env bash

set -e

run_simple() {
  exec python app.py
}

run_gunicorn() {
  exec gunicorn wsgi:app
}

parse_args() {
  mode=simple
  while  [[ $# -gt 0 ]]; do
    case $1 in
      --gunicorn) mode=gunicorn ;;
      *) ;;
    esac
    shift
  done
}

main() {
  parse_args "$@"
  case "${mode}" in
    simple) run_simple ;;
    gunicorn) run_gunicorn ;;
    *) ;;
  esac
}

main "$@"