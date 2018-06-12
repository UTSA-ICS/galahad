from flask import Blueprint, url_for
from flask import abort, redirect, render_template
from ..auth import require_login, current_user
from ..models import OAuth2Client
from ..forms.client import (
    Client2Form, OAuth2ClientWrapper
)

bp = Blueprint('client', __name__)


@bp.route('')
@require_login
def list_clients():
    q = OAuth2Client.query.filter_by(user_id=current_user.id)
    oauth2_clients = q.order_by(OAuth2Client.id.desc()).limit(50).all()
    return render_template(
        'client/list.html',
        oauth2_clients=oauth2_clients,
    )


@bp.route('/<int:version>/create', methods=['GET', 'POST'])
@require_login
def create_client(version):
    form = Client2Form()

    if form.validate_on_submit():
        form.save(current_user)
        return redirect(url_for('.list_clients'))
    return render_template('client/create.html', form=form)


@bp.route('/<int:version>/<client_id>', methods=['GET', 'POST'])
@require_login
def edit_client(version, client_id):
    client = OAuth2Client.query.filter_by(client_id=client_id).first()
    print('WAT    : REDIRECT_URIS - bp.route    : %s' % ''.join(client.redirect_uris))
    if not client or client.user_id != current_user.id:
        abort(404)
    form = Client2Form(obj=OAuth2ClientWrapper(client))

    if form.validate_on_submit():
        form.update(client)
        return redirect(url_for('.list_clients'))
    return render_template('client/edit.html', form=form)
