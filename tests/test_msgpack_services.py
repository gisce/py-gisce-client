# -*- coding: utf-8 -*-
from __future__ import absolute_import
import responses
from gisce.msgpack import MsgPackClient


class TestMsgPackServices(object):
    def _mock_client_bootstrap(self):
        responses.add(
            responses.POST,
            'http://localhost:5000/common',
            json=1,
            status=200,
        )
        responses.add(
            responses.POST,
            'http://localhost:5000/object',
            json=[],
            status=200,
        )

    @responses.activate
    def test_common_service_uses_raw_payload_by_default(self):
        self._mock_client_bootstrap()
        responses.add(
            responses.POST,
            'http://localhost:5000/common',
            json={'feature_a': {'name': 'feature_a'}},
            status=200,
        )

        client = MsgPackClient(
            url='http://localhost:5000',
            database='db',
            user='admin',
            password='secret',
            content_type='json',
        )
        result = client.common.check_for_features(['feature_a'])

        assert result == {'feature_a': {'name': 'feature_a'}}
        assert responses.calls[2].request.body == (
            b'["check_for_features", ["feature_a"]]'
        )

    @responses.activate
    def test_report_service_uses_authenticated_payload_by_default(self):
        self._mock_client_bootstrap()
        responses.add(
            responses.POST,
            'http://localhost:5000/report',
            json='report-id',
            status=200,
        )

        client = MsgPackClient(
            url='http://localhost:5000',
            database='db',
            user='admin',
            password='secret',
            content_type='json',
        )
        result = client.service('report').report('report.name', [1], {}, {})

        assert result == 'report-id'
        assert responses.calls[2].request.body == (
            b'["report", "db", 1, "secret", "report.name", [1], {}, {}]'
        )

    @responses.activate
    def test_service_authentication_can_be_forced(self):
        self._mock_client_bootstrap()
        responses.add(
            responses.POST,
            'http://localhost:5000/common',
            json=True,
            status=200,
        )

        client = MsgPackClient(
            url='http://localhost:5000',
            database='db',
            user='admin',
            password='secret',
            content_type='json',
        )
        result = client.service('common', authenticated=True).ir_del(12)

        assert result is True
        assert responses.calls[2].request.body == (
            b'["ir_del", "db", 1, "secret", 12]'
        )
