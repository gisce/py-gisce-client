# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
import pytest
import responses
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock


class TestIsInteractive(object):
    """Tests for gisce.compat.is_interactive()"""

    def test_returns_true_when_sys_ps1_present(self):
        from gisce.compat import is_interactive
        with patch.object(sys, 'ps1', '>>> ', create=True):
            assert is_interactive() is True

    def test_returns_true_when_stdin_is_tty(self):
        from gisce.compat import is_interactive
        mock_stdin = Mock()
        mock_stdin.isatty.return_value = True
        # Ensure ps1 is absent so only the isatty branch triggers
        had_ps1 = hasattr(sys, 'ps1')
        if had_ps1:
            original_ps1 = sys.ps1
            del sys.ps1
        try:
            with patch('sys.stdin', mock_stdin):
                result = is_interactive()
        finally:
            if had_ps1:
                sys.ps1 = original_ps1
        assert result is True

    def test_returns_false_when_stdin_not_tty_and_no_ps1(self):
        from gisce.compat import is_interactive
        mock_stdin = Mock()
        mock_stdin.isatty.return_value = False
        # Patch builtins so get_ipython is absent
        import builtins
        with patch.object(builtins, 'get_ipython', None, create=True), \
             patch('sys.stdin', mock_stdin):
            # Temporarily remove ps1 if present
            had_ps1 = hasattr(sys, 'ps1')
            if had_ps1:
                original_ps1 = sys.ps1
                del sys.ps1
            try:
                result = is_interactive()
            finally:
                if had_ps1:
                    sys.ps1 = original_ps1
            assert result is False

    def test_returns_true_when_ipython_available_in_builtins(self):
        from gisce.compat import is_interactive
        import builtins
        mock_get_ipython = Mock(return_value=Mock())
        mock_stdin = Mock()
        mock_stdin.isatty.return_value = False
        with patch.object(builtins, 'get_ipython', mock_get_ipython, create=True), \
             patch('sys.stdin', mock_stdin):
            had_ps1 = hasattr(sys, 'ps1')
            if had_ps1:
                original_ps1 = sys.ps1
                del sys.ps1
            try:
                result = is_interactive()
            finally:
                if had_ps1:
                    sys.ps1 = original_ps1
            assert result is True

    def test_returns_false_when_ipython_returns_none(self):
        from gisce.compat import is_interactive
        import builtins
        mock_get_ipython = Mock(return_value=None)
        mock_stdin = Mock()
        mock_stdin.isatty.return_value = False
        with patch.object(builtins, 'get_ipython', mock_get_ipython, create=True), \
             patch('sys.stdin', mock_stdin):
            had_ps1 = hasattr(sys, 'ps1')
            if had_ps1:
                original_ps1 = sys.ps1
                del sys.ps1
            try:
                result = is_interactive()
            finally:
                if had_ps1:
                    sys.ps1 = original_ps1
            assert result is False


class TestGetPassword(object):
    """Tests for gisce.compat.get_password()"""

    def test_returns_provided_password_unchanged(self):
        from gisce.compat import get_password
        assert get_password('admin', 'secret') == 'secret'

    def test_prompts_and_returns_when_interactive_and_no_password(self):
        from gisce.compat import get_password
        with patch('gisce.compat.is_interactive', return_value=True), \
             patch('gisce.compat.prompt_password', return_value='prompted') as mock_prompt:
            result = get_password('admin', None)
        assert result == 'prompted'
        mock_prompt.assert_called_once()

    def test_raises_when_not_interactive_and_no_password(self):
        from gisce.compat import get_password
        with patch('gisce.compat.is_interactive', return_value=False):
            with pytest.raises(ValueError) as exc_info:
                get_password('admin', None)
        assert 'admin' in str(exc_info.value)

    def test_raises_when_not_interactive_and_empty_password(self):
        from gisce.compat import get_password
        with patch('gisce.compat.is_interactive', return_value=False):
            with pytest.raises(ValueError):
                get_password('admin', '')

    def test_error_message_includes_username(self):
        from gisce.compat import get_password
        with patch('gisce.compat.is_interactive', return_value=False):
            with pytest.raises(ValueError) as exc_info:
                get_password('myuser', None)
        assert 'myuser' in str(exc_info.value)

    def test_does_not_prompt_when_password_provided(self):
        from gisce.compat import get_password
        with patch('gisce.compat.prompt_password') as mock_prompt:
            get_password('admin', 'already_set')
        mock_prompt.assert_not_called()


class TestXmlRpcClientPasswordBehavior(object):
    """Tests for password handling in XmlRpcClient.__init__"""

    def _make_client(self, **kwargs):
        from gisce.xmlrpc import XmlRpcClient
        with patch('gisce.xmlrpc.ServerProxy') as mock_sp:
            mock_common = Mock()
            mock_common.login.return_value = 1
            mock_object = Mock()
            mock_object.obj_list.return_value = []
            mock_report = Mock()

            def factory(url, **kw):
                if 'common' in url:
                    return mock_common
                elif 'report' in url:
                    return mock_report
                return mock_object

            mock_sp.side_effect = factory
            return XmlRpcClient(**kwargs)

    def test_login_with_user_and_password(self):
        client = self._make_client(
            url='http://localhost:8069',
            database='db',
            user='admin',
            password='secret'
        )
        assert client.uid == 1
        assert client.password == 'secret'

    def test_raises_when_no_password_non_interactive(self):
        from gisce.xmlrpc import XmlRpcClient
        with patch('gisce.compat.is_interactive', return_value=False):
            with patch('gisce.xmlrpc.ServerProxy'):
                with pytest.raises(ValueError) as exc_info:
                    XmlRpcClient(
                        url='http://localhost:8069',
                        database='db',
                        user='admin'
                    )
        assert 'admin' in str(exc_info.value)

    def test_prompts_when_no_password_interactive(self):
        from gisce.xmlrpc import XmlRpcClient
        with patch('gisce.compat.is_interactive', return_value=True), \
             patch('gisce.compat.prompt_password', return_value='prompted'), \
             patch('gisce.xmlrpc.ServerProxy') as mock_sp:
            mock_common = Mock()
            mock_common.login.return_value = 42
            mock_object = Mock()
            mock_object.obj_list.return_value = []
            mock_report = Mock()

            def factory(url, **kw):
                if 'common' in url:
                    return mock_common
                elif 'report' in url:
                    return mock_report
                return mock_object

            mock_sp.side_effect = factory
            client = XmlRpcClient(
                url='http://localhost:8069',
                database='db',
                user='admin'
            )
        assert client.uid == 42
        assert client.password == 'prompted'

    def test_token_skips_password_prompt(self):
        client = self._make_client(
            url='http://localhost:8069',
            database='db',
            token='mytoken'
        )
        assert client.uid == 'token'
        assert client.password == 'mytoken'


class TestMsgPackClientPasswordBehavior(object):
    """Tests for password handling in MsgPackClient.__init__"""

    def _mock_responses(self):
        responses.add(responses.POST, 'http://localhost:5000/common', json=1, status=200)
        responses.add(responses.POST, 'http://localhost:5000/object', json=[], status=200)

    @responses.activate
    def test_login_with_user_and_password(self):
        from gisce.msgpack import MsgPackClient
        self._mock_responses()
        client = MsgPackClient(
            url='http://localhost:5000',
            database='db',
            user='admin',
            password='secret',
            content_type='json'
        )
        assert client.uid == 1
        assert client.password == 'secret'

    def test_raises_when_no_password_non_interactive(self):
        from gisce.msgpack import MsgPackClient
        with patch('gisce.compat.is_interactive', return_value=False):
            with pytest.raises(ValueError) as exc_info:
                MsgPackClient(
                    url='http://localhost:5000',
                    database='db',
                    user='admin',
                    content_type='json'
                )
        assert 'admin' in str(exc_info.value)

    @responses.activate
    def test_prompts_when_no_password_interactive(self):
        from gisce.msgpack import MsgPackClient
        self._mock_responses()
        with patch('gisce.compat.is_interactive', return_value=True), \
             patch('gisce.compat.prompt_password', return_value='prompted'):
            client = MsgPackClient(
                url='http://localhost:5000',
                database='db',
                user='admin',
                content_type='json'
            )
        assert client.uid == 1
        assert client.password == 'prompted'

    @responses.activate
    def test_token_skips_password_prompt(self):
        from gisce.msgpack import MsgPackClient
        responses.add(responses.POST, 'http://localhost:5000/object', json=[], status=200)
        client = MsgPackClient(
            url='http://localhost:5000',
            database='db',
            token='mytoken',
            content_type='json'
        )
        assert client.uid == 'token'
        assert client.password == 'mytoken'


class TestRequestsClientPasswordBehavior(object):
    """Tests for password handling in RequestsClient.__init__ (via RestApiClient)"""

    @responses.activate
    def test_login_with_user_and_password(self):
        from gisce.restapi import RestApiClient
        responses.add(
            responses.POST, 'http://localhost:5000/ResModel/fields_get',
            json={}, status=200
        )
        client = RestApiClient(
            url='http://localhost:5000',
            user='admin',
            password='secret'
        )
        assert client.auth == ('admin', 'secret')

    def test_raises_when_no_password_non_interactive(self):
        from gisce.restapi import RestApiClient
        with patch('gisce.compat.is_interactive', return_value=False):
            with pytest.raises(ValueError) as exc_info:
                RestApiClient(
                    url='http://localhost:5000',
                    user='admin'
                )
        assert 'admin' in str(exc_info.value)

    @responses.activate
    def test_prompts_when_no_password_interactive(self):
        from gisce.restapi import RestApiClient
        with patch('gisce.compat.is_interactive', return_value=True), \
             patch('gisce.compat.prompt_password', return_value='prompted'):
            client = RestApiClient(
                url='http://localhost:5000',
                user='admin'
            )
        assert client.auth == ('admin', 'prompted')

    @responses.activate
    def test_token_auth_skips_password_prompt(self):
        from gisce.restapi import RestApiClient
        client = RestApiClient(
            url='http://localhost:5000',
            token='mytoken'
        )
        assert 'Authorization' in client.headers
        assert client.headers['Authorization'] == 'token mytoken'
