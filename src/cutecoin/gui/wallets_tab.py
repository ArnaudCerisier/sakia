"""
Created on 15 févr. 2015

@author: inso
"""
import asyncio
import logging

from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication, QDialog, QMessageBox
from PyQt5.QtCore import QDateTime, QModelIndex, Qt, QLocale
from PyQt5.QtGui import QCursor

from ..core.registry import Identity
from ..core.wallet import Wallet
from cutecoin.gui import toast
from ..gui.password_asker import PasswordAskerDialog
from ..models.wallets import WalletsTableModel, WalletsFilterProxyModel
from .transfer import TransferMoneyDialog
from ..tools.exceptions import MembershipNotFoundError, NoPeerAvailable, LookupFailureError
from ..gen_resources.wallets_tab_uic import Ui_WalletsTab


class WalletsTabWidget(QWidget, Ui_WalletsTab):
    """
    classdocs
    """

    def __init__(self, app, account, community, password_asker):
        """
        Init
        :param cutecoin.core.app.Application app: Application instance
        :param cutecoin.core.account.Account account: Account instance
        :param cutecoin.core.community.Community community: Community instance
        :param cutecoin.gui.password_asker.PasswordAskerDialog password_asker: PasswordAskerDialog instance
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = account
        self.community = community
        self.password_asker = password_asker
        self.setup_connections()

    def setup_connections(self):
        self.account.inner_data_changed.connect(self.refresh_informations_frame)
        self.community.inner_data_changed.connect(self.refresh_informations_frame)

    def refresh(self):
        self.refresh_informations_frame()
        self.refresh_wallets()
        self.refresh_quality_buttons()

    def refresh_wallets(self):
        # TODO: Using reset model instead of destroy/create
        wallets_model = WalletsTableModel(self.app, self.community)
        proxy_model = WalletsFilterProxyModel()
        proxy_model.setSourceModel(wallets_model)
        wallets_model.dataChanged.connect(self.wallet_changed)
        self.table_wallets.setModel(proxy_model)
        self.table_wallets.resizeColumnsToContents()

    def refresh_informations_frame(self):
        parameters = self.community.parameters
        try:
            identity = self.account.identity(self.community)
            membership = identity.membership(self.community)
            renew_block = membership['blockNumber']
            last_renewal = self.community.get_block(renew_block)['medianTime']
            expiration = last_renewal + parameters['sigValidity']
        except MembershipNotFoundError:
            last_renewal = None
            expiration = None

        certified = identity.unique_valid_certified_by(self.app.identities_registry, self.community)
        certifiers = identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
        if last_renewal and expiration:
            date_renewal = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(last_renewal).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )
            date_expiration = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(expiration).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )

            if self.account.pubkey in self.community.members_pubkeys():
                # set infos in label
                self.label_general.setText(
                    self.tr("""
                    <table cellpadding="5">
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    </table>
                    """).format(
                        self.account.name, self.account.pubkey,
                        self.tr("Membership"),
                        self.tr("Last renewal on {:}, expiration on {:}").format(date_renewal, date_expiration),
                        self.tr("Your web of trust"),
                        self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                    )
                )
            else:
                # set infos in label
                self.label_general.setText(
                    self.tr("""
                    <table cellpadding="5">
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    </table>
                    """).format(
                        self.account.name, self.account.pubkey,
                        self.tr("Not a member"),
                        self.tr("Last renewal on {:}, expiration on {:}").format(date_renewal, date_expiration),
                        self.tr("Your web of trust"),
                        self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                    )
                )
        else:
            # set infos in label
            self.label_general.setText(
                self.tr("""
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """).format(
                    self.account.name, self.account.pubkey,
                    self.tr("Not a member"),
                    self.tr("Your web of trust"),
                    self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                         len(certified))
                )
            )

        amount = self.account.amount(self.community)
        maximum = self.community.monetary_mass
        # if referential type is quantitative...
            # display int values
        localized_amount = self.account.current_ref(amount, self.community, self.app).localized(units=True)
        localized_minimum = self.account.current_ref(0, self.community, self.app).localized(units=True)
        localized_maximum = self.account.current_ref(maximum, self.community, self.app).localized(units=True)

        # set infos in label
        self.label_balance.setText(
            self.tr("{:}")
            .format(
                localized_amount
            )
        )
        self.label_balance_range.setText(
            self.tr("in [{:} ; {:}]")
            .format(
                localized_minimum,
                localized_maximum
            )
        )

    def wallet_context_menu(self, point):
        index = self.table_wallets.indexAt(point)
        model = self.table_wallets.model()
        if index.row() < model.rowCount(QModelIndex()):
            source_index = model.mapToSource(index)

            name_col = model.sourceModel().columns_types.index('name')
            name_index = model.index(index.row(),
                                     name_col)

            pubkey_col = model.sourceModel().columns_types.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                     pubkey_col)

            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            menu = QMenu(model.data(index, Qt.DisplayRole), self)

            new_wallet = QAction(self.tr("New Wallet"), self)
            new_wallet.triggered.connect(self.new_wallet)

            rename = QAction(self.tr("Rename"), self)
            rename.triggered.connect(self.rename_wallet)
            rename.setData(name_index)

            copy_pubkey = QAction(self.tr("Copy pubkey to clipboard"), self)
            copy_pubkey.triggered.connect(self.copy_pubkey_to_clipboard)
            copy_pubkey.setData(pubkey)

            transfer_to = QMenu()
            transfer_to.setTitle(self.tr("Transfer to..."))
            for w in self.account.wallets:
                if w == self.account.wallets[source_index.row()]:
                    continue
                transfer_action = QAction(w.name, self)
                transfer_action.triggered.connect(self.transfer_to_wallet)
                wallets = (self.account.wallets[source_index.row()], w)
                transfer_action.setData(wallets)
                transfer_to.addAction(transfer_action)

            menu.addAction(new_wallet)
            menu.addAction(rename)
            menu.addAction(copy_pubkey)
            menu.addMenu(transfer_to)
            # Show the context menu.
            menu.exec_(QCursor.pos())

    def new_wallet(self):
        """
        Create a new wallet
        """
        password_asker = PasswordAskerDialog(self.app.current_account)
        password = password_asker.exec_()
        if password_asker.result() == QDialog.Rejected:
            return None
        # create new wallet by increasing wallet pool size
        self.account.set_walletpool_size(len(self.account.wallets) + 1, password)
        # capture new wallet
        wallet = self.account.wallets[len(self.account.wallets) - 1]
        # feed cache data of the wallet
        wallet.refresh_cache(self.community, list())
        # save wallet cache on disk
        self.app.save_wallet(self.account, self.account.wallets[len(self.account.wallets) - 1])
        # save account cache on disk (update number of wallets)
        self.app.save(self.account)
        # refresh wallet list in gui
        self.refresh()

    def rename_wallet(self):
        index = self.sender().data()
        self.table_wallets.edit(index)

    def wallet_changed(self):
        self.table_wallets.resizeColumnsToContents()
        self.app.save(self.app.current_account)

    def copy_pubkey_to_clipboard(self):
        data = self.sender().data()
        clipboard = QApplication.clipboard()
        if data.__class__ is Wallet:
            clipboard.setText(data.pubkey)
        elif data.__class__ is Identity:
            clipboard.setText(data.pubkey)
        elif data.__class__ is str:
            clipboard.setText(data)

    def transfer_to_wallet(self):
        wallets = self.sender().data()
        dialog = TransferMoneyDialog(self.app, self.account, self.password_asker)
        dialog.edit_pubkey.setText(wallets[1].pubkey)
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.combo_wallets.setCurrentText(wallets[0].name)
        dialog.radio_pubkey.setChecked(True)
        if dialog.exec_() == QDialog.Accepted:
            currency_tab = self.window().currencies_tabwidget.currentWidget()
            currency_tab.tab_history.table_history.model().sourceModel().refresh_transfers()

    def send_membership_demand(self):
        password = self.password_asker.exec_()
        if self.password_asker.result() == QDialog.Rejected:
            return
        asyncio.async(self.account.send_membership(password, self.community, 'IN'))

    def send_membership_leaving(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Sending a leaving demand  cannot be canceled.
The process to join back the community later will have to be done again.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            asyncio.async(self.account.send_membership(password, self.community, 'OUT'))

    def publish_uid(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Publishing your UID can be canceled by Revoke UID.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            try:
                self.account.send_selfcert(password, self.community)
                toast.display(self.tr("UID Publishing"),
                              self.tr("Success publishing your UID"))
            except ValueError as e:
                QMessageBox.critical(self, self.tr("Publish UID error"),
                                  str(e))
            except NoPeerAvailable as e:
                QMessageBox.critical(self, self.tr("Network error"),
                                     self.tr("Couldn't connect to network : {0}").format(e),
                                     QMessageBox.Ok)
            # except Exception as e:
            #     QMessageBox.critical(self, self.tr("Error"),
            #                          "{0}".format(e),
            #                          QMessageBox.Ok)

    def revoke_uid(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                                 self.tr("""Are you sure ?
Revoking your UID can only success if it is not already validated by the network.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            asyncio.async(self.account.revoke(password, self.community))

    def refresh_quality_buttons(self):
        try:
            if self.account.identity(self.community).published_uid(self.community):
                logging.debug("UID Published")
                if self.account.identity(self.community).is_member(self.community):
                    self.button_membership.setText(self.tr("Renew membership"))
                    self.button_membership.show()
                    self.button_publish_uid.hide()
                    self.button_leaving.show()
                    self.button_revoke_uid.hide()
                else:
                    logging.debug("Not a member")
                    self.button_membership.setText(self.tr("Send membership demand"))
                    self.button_membership.show()
                    self.button_revoke_uid.show()
                    self.button_leaving.hide()
                    self.button_publish_uid.hide()
            else:
                logging.debug("UID not published")
                self.button_membership.hide()
                self.button_leaving.hide()
                self.button_publish_uid.show()
                self.button_revoke_uid.hide()
        except LookupFailureError:
            self.button_membership.hide()
            self.button_leaving.hide()
            self.button_publish_uid.show()
