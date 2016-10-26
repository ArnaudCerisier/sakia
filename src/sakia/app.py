"""
Created on 1 févr. 2014

@author: inso
"""

import datetime
import logging

import aiohttp
from PyQt5.QtCore import QObject, pyqtSignal, QTranslator, QCoreApplication, QLocale
from aiohttp.connector import ProxyConnector

from duniterpy.api.bma import API
from . import __version__
from .options import SakiaOptions
from sakia.data.connectors import BmaConnector
from sakia.services import NetworkService, BlockchainService, IdentitiesService, SourcesServices
from sakia.data.repositories import SakiaDatabase
from sakia.data.processors import BlockchainProcessor, NodesProcessor, IdentitiesProcessor, \
    CertificationsProcessor, SourcesProcessor
from sakia.data.files import AppDataFile, UserParametersFile
from sakia.decorators import asyncify
from sakia.money import Relative


class Application(QObject):

    """
    Managing core application datas :
    Accounts list and general configuration
    Saving and loading the application state
    """

    def __init__(self, qapp, loop, options, app_data, parameters, db,
                 network_services, blockchain_services, identities_services):
        """
        Init a new "sakia" application
        :param QCoreApplication qapp: Qt Application
        :param quamash.QEventLoop loop: quamash.QEventLoop instance
        :param sakia.options.SakiaOptions options: the options
        :param sakia.data.entities.AppData app_data: the application data
        :param sakia.data.entities.UserParameters parameters: the application current user parameters
        :param sakia.data.repositories.SakiaDatabase db: The database
        :param dict network_services: All network services for current currency
        :param dict blockchain_services: All network services for current currency
        :param dict identities_services: All network services for current currency
        :return:
        """
        super().__init__()
        self.qapp = qapp
        self.loop = loop
        self.options = options
        self.available_version = (True,
                                  __version__,
                                  "")
        self._translator = QTranslator(self.qapp)
        self._app_data = app_data
        self._parameters = parameters
        self.db = db
        self.network_services = network_services
        self.blockchain_services = blockchain_services
        self.identities_services = identities_services

    @classmethod
    def startup(cls, argv, qapp, loop):
        options = SakiaOptions.from_arguments(argv)
        app_data = AppDataFile.in_config_path(options.config_path).load_or_init()
        app = cls(qapp, loop, options, app_data, None, None, {}, {}, {})
        #app.set_proxy()
        #app.get_last_version()
        app.load_profile(app_data.default)
        #app.switch_language()
        return app

    def load_profile(self, profile_name):
        """
        Initialize databases depending on profile loaded
        :param profile_name:
        :return:
        """
        self._parameters = UserParametersFile.in_config_path(self.options.config_path, profile_name).load_or_init()
        self.db = SakiaDatabase.load_or_init(self.options.config_path, profile_name)

        nodes_processor = NodesProcessor(self.db.nodes_repo)
        bma_connector = BmaConnector(nodes_processor)
        identities_processor = IdentitiesProcessor(self.db.identities_repo, self.db.blockchains_repo, bma_connector)
        certs_processor = CertificationsProcessor(self.db.certifications_repo, self.db.identities_repo, bma_connector)
        blockchain_processor = BlockchainProcessor.instanciate(self)
        sources_processor = SourcesProcessor.instanciate(self)

        self.blockchain_services = {}
        self.network_services = {}
        self.identities_services = {}
        self.sources_services = {}
        for currency in self.db.connections_repo.get_currencies():
            self.identities_services[currency] = IdentitiesService(currency, identities_processor,
                                                                   certs_processor, blockchain_processor,
                                                                   bma_connector)
            self.blockchain_services[currency] = BlockchainService(currency, blockchain_processor, bma_connector,
                                                                   self.identities_services[currency])
            self.network_services[currency] = NetworkService.load(currency, nodes_processor,
                                                                  self.blockchain_services[currency])
            self.sources_services[currency] = SourcesServices(currency, sources_processor, bma_connector)

    def set_proxy(self):
        if self.preferences['enable_proxy'] is True:
            API.aiohttp_connector = ProxyConnector("http://{0}:{1}".format(
                                    self.preferences['proxy_address'],
                                    self.preferences['proxy_port']))
        else:
            API.aiohttp_connector = None

    def switch_language(self):
        logging.debug("Loading translations")
        locale = self.preferences['lang']
        QLocale.setDefault(QLocale(locale))
        QCoreApplication.removeTranslator(self._translator)
        self._translator = QTranslator(self.qapp)
        if locale == "en_GB":
            QCoreApplication.installTranslator(self._translator)
        elif self._translator.load(":/i18n/{0}".format(locale)):
            if QCoreApplication.installTranslator(self._translator):
                logging.debug("Loaded i18n/{0}".format(locale))
            else:
                logging.debug("Couldn't load translation")

    @property
    def parameters(self):
        """
        :rtype: sakia.data.entities.UserParameters
        """
        return self._parameters

    def start_coroutines(self):
        for currency in self.connections_repo.get_currencies():
            self.network_services[currency].start_coroutines()

    async def stop_current_profile(self, closing=False):
        """
        Save the account to the cache
        and stop the coroutines
        """
        for currency in self.connections_repo.get_currencies():
            await self.network_services[currency].stop_coroutines(closing)

    @asyncify
    async def get_last_version(self):
        if self.preferences['enable_proxy'] is True:
            connector = ProxyConnector("http://{0}:{1}".format(
                                    self.preferences['proxy_address'],
                                    self.preferences['proxy_port']))
        else:
            connector = None
        try:
            with aiohttp.Timeout(15):
                response = await aiohttp.get("https://api.github.com/repos/duniter/sakia/releases", connector=connector)
                if response.status == 200:
                    releases = await response.json()
                    latest = None
                    for r in releases:
                        if not latest:
                            latest = r
                        else:
                            latest_date = datetime.datetime.strptime(latest['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                            date = datetime.datetime.strptime(r['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                            if latest_date < date:
                                latest = r
                    latest_version = latest["tag_name"]
                    version = (__version__ == latest_version,
                               latest_version,
                               latest["html_url"])
                    logging.debug("Found version : {0}".format(latest_version))
                    logging.debug("Current version : {0}".format(__version__))
                    self.available_version = version
                self.version_requested.emit()
        except (aiohttp.errors.ClientError, aiohttp.errors.TimeoutError) as e:
            logging.debug("Could not connect to github : {0}".format(str(e)))
        except Exception as e:
            pass

    @property
    def current_ref(self):
        return Relative