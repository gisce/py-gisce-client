# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import sys
import pytest
import responses
try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock
from gisce.cli import main, build_parser


class TestBuildParser(object):
    """Tests for the argument parser"""

    def test_required_args(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_user_auth(self):
        parser = build_parser()
        args = parser.parse_args([
            '--url', 'https+xmlrpc://erp.example.com',
            '--database', 'mydb',
            '--user', 'admin',
            '--password', 'secret',
            '--model', 'res.users',
            '--method', 'search',
        ])
        assert args.url == 'https+xmlrpc://erp.example.com'
        assert args.database == 'mydb'
        assert args.user == 'admin'
        assert args.password == 'secret'
        assert args.model == 'res.users'
        assert args.method == 'search'
        assert args.args == '[]'
        assert args.kwargs == '{}'
        assert not args.no_verify

    def test_parses_token_auth(self):
        parser = build_parser()
        args = parser.parse_args([
            '--url', 'https+xmlrpc://erp.example.com',
            '--database', 'mydb',
            '--token', 'mytoken',
            '--model', 'res.users',
            '--method', 'search',
        ])
        assert args.token == 'mytoken'
        assert args.user is None

    def test_user_and_token_are_mutually_exclusive(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--user', 'admin',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
            ])

    def test_no_verify_flag(self):
        parser = build_parser()
        args = parser.parse_args([
            '--url', 'https+xmlrpc://erp.example.com',
            '--database', 'mydb',
            '--token', 'mytoken',
            '--model', 'res.users',
            '--method', 'search',
            '--no-verify',
        ])
        assert args.no_verify

    def test_parses_args_and_kwargs(self):
        parser = build_parser()
        args = parser.parse_args([
            '--url', 'https+xmlrpc://erp.example.com',
            '--database', 'mydb',
            '--token', 'mytoken',
            '--model', 'res.users',
            '--method', 'read',
            '--args', '[[1, 2, 3]]',
            '--kwargs', '{"fields": ["name"]}',
        ])
        assert args.args == '[[1, 2, 3]]'
        assert args.kwargs == '{"fields": ["name"]}'

    def test_short_flags(self):
        parser = build_parser()
        args = parser.parse_args([
            '--url', 'https+xmlrpc://erp.example.com',
            '-d', 'mydb',
            '-u', 'admin',
            '-p', 'secret',
            '-m', 'res.users',
            '--method', 'search',
        ])
        assert args.database == 'mydb'
        assert args.user == 'admin'
        assert args.password == 'secret'
        assert args.model == 'res.users'


class TestMain(object):
    """Integration-style tests for the main() entry point"""

    def test_missing_password_with_user_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--user', 'admin',
                '--model', 'res.users',
                '--method', 'search',
            ])
        assert exc_info.value.code != 0

    def test_invalid_args_json_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
                '--args', 'not-json',
            ])
        assert exc_info.value.code != 0

    def test_invalid_kwargs_json_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
                '--kwargs', 'not-json',
            ])
        assert exc_info.value.code != 0

    def test_args_not_list_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
                '--args', '{"not": "a list"}',
            ])
        assert exc_info.value.code != 0

    def test_kwargs_not_dict_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
                '--kwargs', '[1, 2, 3]',
            ])
        assert exc_info.value.code != 0

    def test_unsupported_protocol_exits(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([
                '--url', 'ftp://erp.example.com',
                '--database', 'mydb',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
            ])
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert 'Unsupported protocol' in captured.err

    def test_successful_call_with_token(self, capsys):
        mock_result = [1, 2, 3]
        mock_model = MagicMock()
        mock_model.search.return_value = mock_result
        mock_client = MagicMock()
        mock_client.model.return_value = mock_model

        with patch('gisce.cli.connect', return_value=mock_client) as mock_connect:
            main([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
                '--args', '[[]]',
            ])

        mock_connect.assert_called_once_with(
            'https+xmlrpc://erp.example.com',
            'mydb',
            verify=True,
            token='mytoken',
        )
        mock_client.model.assert_called_once_with('res.users')
        mock_model.search.assert_called_once_with([])

        captured = capsys.readouterr()
        assert json.loads(captured.out) == mock_result

    def test_successful_call_with_user_password(self, capsys):
        mock_result = {'name': 'Admin'}
        mock_model = MagicMock()
        mock_model.read.return_value = mock_result
        mock_client = MagicMock()
        mock_client.model.return_value = mock_model

        with patch('gisce.cli.connect', return_value=mock_client):
            main([
                '--url', 'https+restapi://erp.example.com',
                '--database', 'mydb',
                '--user', 'admin',
                '--password', 'secret',
                '--model', 'res.users',
                '--method', 'read',
                '--args', '[[1]]',
                '--kwargs', '{"fields": ["name"]}',
            ])

        captured = capsys.readouterr()
        assert json.loads(captured.out) == mock_result

    def test_connect_error_exits(self, capsys):
        with patch('gisce.cli.connect', side_effect=Exception('connection refused')):
            with pytest.raises(SystemExit) as exc_info:
                main([
                    '--url', 'https+xmlrpc://erp.example.com',
                    '--database', 'mydb',
                    '--token', 'mytoken',
                    '--model', 'res.users',
                    '--method', 'search',
                ])
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert 'Error connecting' in captured.err

    def test_method_call_error_exits(self, capsys):
        mock_model = MagicMock()
        mock_model.search.side_effect = Exception('access denied')
        mock_client = MagicMock()
        mock_client.model.return_value = mock_model

        with patch('gisce.cli.connect', return_value=mock_client):
            with pytest.raises(SystemExit) as exc_info:
                main([
                    '--url', 'https+xmlrpc://erp.example.com',
                    '--database', 'mydb',
                    '--token', 'mytoken',
                    '--model', 'res.users',
                    '--method', 'search',
                ])
        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert 'Error calling' in captured.err

    def test_no_verify_passed_to_connect(self, capsys):
        mock_client = MagicMock()
        mock_client.model.return_value = MagicMock()
        mock_client.model.return_value.search.return_value = []

        with patch('gisce.cli.connect', return_value=mock_client) as mock_connect:
            main([
                '--url', 'https+xmlrpc://erp.example.com',
                '--database', 'mydb',
                '--token', 'mytoken',
                '--model', 'res.users',
                '--method', 'search',
                '--no-verify',
            ])

        mock_connect.assert_called_once_with(
            'https+xmlrpc://erp.example.com',
            'mydb',
            verify=False,
            token='mytoken',
        )
