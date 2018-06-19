from flask import Blueprint, request
from flask import jsonify, render_template
from authlib.specs.rfc6749 import OAuth2Error
from ..models import OAuth2Client
from ..auth import current_user
from ..forms.auth import ConfirmForm, LoginConfirmForm
from ..services.oauth2 import authorization, scopes

bp = Blueprint('oauth2', __name__)


@bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    if current_user:
        form = ConfirmForm()
        print('WAT    : ConfirmForm() form = %s' % form)
    else:
        form = LoginConfirmForm()
        print('WAT    : LoginConfirmForm() form = %s' % form)

    if form.validate_on_submit():
        grant_user = current_user
        return authorization.create_authorization_response(grant_user=grant_user)
    try:
        grant = authorization.validate_consent_request(end_user=current_user)
    except OAuth2Error as error:
        # TODO: add an error page
        payload = dict(error.get_body())
        return jsonify(payload), error.status_code

    client = OAuth2Client.query.filter_by(id=request.args['client_id']).first()
    return render_template(
        'account/authorize.html',
        grant=grant,
        scopes=scopes,
        client=client,
        form=form,
    )


@bp.route('/token', methods=['POST'])
def issue_token():
    for a in request.form:
        print('WAT    : %s=%s' % (a, request.form[a]))
    print('WAT    : %s' % request.form)
    return authorization.create_token_response()


@bp.route('/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_revocation_response()
