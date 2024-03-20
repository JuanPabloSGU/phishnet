import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from phishnet.elastic import connect_elasticsearch, close_elasticsearch

bp = Blueprint('auth', __name__, url_prefix='/auth')