import json
import pytest

from pathlib import Path

from app.database import db
from app.main import create_app
from app.models.activation import Activation
from app.models.match import Match
from app.models.match_meta import MatchMeta
from tests.helpers import getMatchData, getProjectedMatrix, getSingleTurnData
from tests.utils import login, newMatch, nextTurn, register, startMatch, viewTurn

TEST_DB = 'test.db'

class TestLiveMatchViewing:
    @pytest.fixture
    def client(self):
        BASE_DIR = Path(__file__).resolve().parent.parent

        self.app = create_app()

        self.app.config['TESTING'] = True
        self.app.config['DATABASE'] = BASE_DIR.joinpath(TEST_DB)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BASE_DIR.joinpath(TEST_DB)}'

        self.app.config['EMAIL'] = 'admin@test.com'
        self.app.config['USERNAME'] = 'admin'
        self.app.config['PASSWORD'] = 'password'
        self.app.config['ACTIVATION_KEY'] = '08fe47e8814b410cbaf742463e8c9252'
        self.app.config['ACTIVATION_KEY_2'] = '97a56754b27e4cbea94e6c7ca9884b2b'

        db.create_all()

        key_first = Activation(self.app.config['ACTIVATION_KEY'])
        key_second = Activation(self.app.config['ACTIVATION_KEY_2'])
        """Use fixed activation key strings for testing purposes."""
        db.session.add(key_first)
        db.session.add(key_second)
        db.session.commit()

        with self.app.test_client(self) as client:
            yield client

        db.drop_all()

    def testViewSingleTurn(self, client):
        rv = register(client, self.app.config['EMAIL'], self.app.config['USERNAME'], self.app.config['PASSWORD'], self.app.config['ACTIVATION_KEY'])
        rv = login(client, self.app.config['EMAIL'], self.app.config['PASSWORD'])

        access_token = json.loads(rv.data)['access_token']
        rv = newMatch(
            client,
            getMatchData(),
            access_token
        )

        uuid = json.loads(rv.data)['uuid']
        response = startMatch(
            client,
            uuid,
            access_token
        )

        rv = nextTurn(
            client,
            uuid,
            getSingleTurnData(),
            access_token
        )

        response = viewTurn(
            client,
            uuid,
            1,
            access_token
        )

        assert 200 == response.status_code
        assert 'Turn data retrieved successfully.' in response.json['message']
        assert response.json['data']

        assert response.json['data']['player_1']
        """Player 1 response data validation."""

        assert response.json['data']['player_1']['characters'][0]
        assert 30 == response.json['data']['player_1']['characters'][0]['health']['current']
        assert 30 == response.json['data']['player_1']['characters'][0]['health']['max']
        assert 'move' in response.json['data']['player_1']['characters'][0]['action']
        assert 1 == response.json['data']['player_1']['characters'][0]['position']['x']
        assert 0 == response.json['data']['player_1']['characters'][0]['position']['y']

        assert response.json['data']['player_1']['characters'][1]
        assert 20 == response.json['data']['player_1']['characters'][1]['health']['current']
        assert 20 == response.json['data']['player_1']['characters'][1]['health']['max']
        assert 'move' in response.json['data']['player_1']['characters'][1]['action']
        assert 1 == response.json['data']['player_1']['characters'][1]['position']['x']
        assert 3 == response.json['data']['player_1']['characters'][1]['position']['y']

        assert response.json['data']['player_1']['characters'][2]
        assert 40 == response.json['data']['player_1']['characters'][2]['health']['current']
        assert 40 == response.json['data']['player_1']['characters'][2]['health']['max']
        assert 'move' in response.json['data']['player_1']['characters'][2]['action']
        assert 1 == response.json['data']['player_1']['characters'][2]['position']['x']
        assert 6 == response.json['data']['player_1']['characters'][2]['position']['y']

        assert response.json['data']['player_2']
        """Player 2 response data validation."""

        assert response.json['data']['player_2']['characters'][0]
        assert 50 == response.json['data']['player_2']['characters'][0]['health']['current']
        assert 50 == response.json['data']['player_2']['characters'][0]['health']['max']
        assert 'move' in response.json['data']['player_2']['characters'][0]['action']
        assert 14 == response.json['data']['player_2']['characters'][0]['position']['x']
        assert 0 == response.json['data']['player_2']['characters'][0]['position']['y']

        assert response.json['data']['player_2']['characters'][1]
        assert 30 == response.json['data']['player_2']['characters'][1]['health']['current']
        assert 30 == response.json['data']['player_2']['characters'][1]['health']['max']
        assert 'move' in response.json['data']['player_2']['characters'][1]['action']
        assert 14 == response.json['data']['player_2']['characters'][1]['position']['x']
        assert 3 == response.json['data']['player_2']['characters'][1]['position']['y']

        assert response.json['data']['player_2']['characters'][2]
        assert 20 == response.json['data']['player_2']['characters'][2]['health']['current']
        assert 20 == response.json['data']['player_2']['characters'][2]['health']['max']
        assert 'move' in response.json['data']['player_2']['characters'][2]['action']
        assert 14 == response.json['data']['player_2']['characters'][2]['position']['x']
        assert 6 == response.json['data']['player_2']['characters'][2]['position']['y']

    def testViewMatrixState(self, client):
        rv = register(client, self.app.config['EMAIL'], self.app.config['USERNAME'], self.app.config['PASSWORD'], self.app.config['ACTIVATION_KEY'])
        rv = login(client, self.app.config['EMAIL'], self.app.config['PASSWORD'])

        access_token = json.loads(rv.data)['access_token']
        rv = newMatch(
            client,
            getMatchData(),
            access_token
        )

        uuid = json.loads(rv.data)['uuid']
        response = startMatch(
            client,
            uuid,
            access_token
        )

        rv = nextTurn(
            client,
            uuid,
            getSingleTurnData(),
            access_token
        )

        response = viewTurn(
            client,
            uuid,
            1,
            access_token
        )

        assert response.json['matrix']

        matrix = getProjectedMatrix()
        same = True
        """Matrix validation setup."""

        for i in range(8):
            """Default battleground size is 16x8 tiles."""
            for actual, provided in zip(response.json['matrix'][i], matrix[i]):
                """Use simple looping of list items to make direct comparisons on each value."""
                if actual != provided:
                    same = False

        assert True == same

    def testViewSingleTurnOtherOwners(self, client):
        rv = register(client, self.app.config['EMAIL'], self.app.config['USERNAME'], self.app.config['PASSWORD'], self.app.config['ACTIVATION_KEY'])
        rv = login(client, self.app.config['EMAIL'], self.app.config['PASSWORD'])

        access_token = json.loads(rv.data)['access_token']
        rv = newMatch(
            client,
            getMatchData(),
            access_token
        )

        uuid = json.loads(rv.data)['uuid']
        response = startMatch(
            client,
            uuid,
            access_token
        )

        response = viewTurn(
            client,
            uuid,
            1,
            access_token
        )

        assert 400 == response.status_code
        """Match hasn't completed any turns yet."""
        assert 'Match does not have any turns completed.' in response.json['message']

        rv = nextTurn(
            client,
            uuid,
            getSingleTurnData(),
            access_token
        )

        new_rv = register(client, '1' + self.app.config['EMAIL'], '1' + self.app.config['USERNAME'], self.app.config['PASSWORD'], self.app.config['ACTIVATION_KEY_2'])
        new_rv = login(client, '1' + self.app.config['EMAIL'], self.app.config['PASSWORD'])

        new_access_token = json.loads(new_rv.data)['access_token']

        response = viewTurn(
            client,
            '',
            1,
            access_token
        )

        assert 404 == response.status_code
        """Cannot view matches that don't exist in the database."""

        response = client.get(
            f'/turn/view/{uuid}/1',
            follow_redirects=False
        )

        assert 401 == response.status_code
        """Test malformed GET request."""

        response = viewTurn(
            client,
            uuid,
            1,
            ''
        )

        assert 422 == response.status_code
        """Cannot view matches without a valid access token."""

        response = viewTurn(
            client,
            uuid,
            1,
            new_access_token
        )

        assert 401 == response.status_code
        """Cannot view matches that were created by other users."""
        assert 'Cannot view matches owned by other users.' in response.json['message']

        response = viewTurn(
            client,
            uuid,
            2,
            access_token
        )

        assert 400 == response.status_code
        assert 'Invalid turn number provided.' in response.json['message']
