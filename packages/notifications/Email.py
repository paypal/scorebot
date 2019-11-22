from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
import traceback

from django.template.loader import get_template

from common import constants


class Email(object):
    """
    Send emails for the service.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def _prepare_email_recipients(self, email_recipients):
        """
        Returns email_recipients correctly formatted in a comma separated string

        :param email_recipients: comma separated lists of email addresses
        :returns string: containing the email_recipients
        """
        recipients = None
        try:
            recipients = email_recipients.replace(',', ' ')
            recipients = recipients.replace(';', ' ')
            recipients = recipients.split()
            recipients = ', '.join(recipients)
        except Exception as e:
            self._logger.error("\n%s: %s\n%s\n" % (type(e), str(e), traceback.format_exc()))

        return recipients

    def send_email(self, template_prefix, subject, recipients, email_info, sender_addr=None):
        """
        Send email using the passed in template and data. Sends both html and plain text versions.

        :param template_prefix: The prefix for the template name to be used
        :param subject: e-mail subject
        :param recipients: A comma delimited list of e-mail addresses
        :param email_info: A data dictionary to be used when rendering the template
        :param sender_addr: Sender's email address (defaults to tool team)
        """
        self._logger.info('send_email')

        self._logger.debug("\ntemplate_prefix: {0}\nsubject: {1}\nrecipients: {2}".format(template_prefix,
                                                                                          subject,
                                                                                          recipients))
        self._logger.debug("\nemail_info: {0}\nsender_addr: {1}".format(email_info, sender_addr))
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            email_info['email_subject'] = subject
            email_info['support_dl'] = constants.SCOREBOT_DL_EMAIL_ADDRESS

            if not sender_addr:
                # If we dont get a sender passed in then we are using our tool support dl
                sender_addr = constants.SCOREBOT_FROM_DL_EMAIL
            email_from = sender_addr
            msg['From'] = email_from

            email_to = self._prepare_email_recipients(recipients)
            msg['To'] = email_to
            email_to_list = [recipient.strip() for recipient in email_to.split(',') if recipient]
            email_to_list.append(constants.SCOREBOT_DL_EMAIL_ADDRESS)

            # HTML email
            template_name = template_prefix + '.html'
            try:
                html_data = get_template(template_name).render(email_info)
                html_content = MIMEText(html_data, 'html')
                msg.attach(html_content)
            except Exception as err:
                self._logger.error("Template Error: {0}\n{1}\n{2}\n".format(template_name, type(err),
                                                                            traceback.format_exc()))
                raise err

            # Text email
            template_name = template_prefix + '.txt'
            try:
                text_data = get_template(template_name).render(email_info)
                text_content = MIMEText(text_data, 'plain')
                msg.attach(text_content)
            except Exception as err:
                self._logger.error("Template Error: {0}\n{1}\n{2}\n".format(template_name,
                                                                            type(err),
                                                                            traceback.format_exc()))
                raise err

            smtp_email = smtplib.SMTP(constants.DEFAULT_SMTP_SERVER, 25, timeout=60)

            try:
                # Uncomment when debugging emails - leave commented otherwise - it is a lot of output.
                # self._logger.debug("\nemail_recipients: {0}\nsubject: {1}\ncontent: {2}".format(email_to_list,
                #                                                                                 subject,
                #                                                                                 msg.as_string()))
                send_result = smtp_email.sendmail(email_from, email_to_list, msg.as_string())
                if len(send_result) > 0:
                    for email_addr, (code, error_msg) in send_result.items():
                        self._logger.error("Deliver failed for: {0} [{1}:{2}]".format(email_addr, code, error_msg))

            except smtplib.SMTPHeloError as err:
                # The server didn't reply properly to the helo greeting.
                self._logger.error("SMTP Server Error\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
                self._logger.error("{0}".format(str(err)))
                raise err

            except smtplib.SMTPServerDisconnected as err:
                self._logger.error("SMTP Disconnected\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
                self._logger.error("{0}".format(str(err)))
                raise err

            except smtplib.SMTPConnectError as err:
                self._logger.error("SMTP Connection Error\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
                self._logger.error("{0}".format(str(err)))
                raise err

            except smtplib.SMTPRecipientsRefused as err:
                # The server rejected ALL recipients - no mail was sent.
                self._logger.error("Recipients rejected\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
                self._logger.error("{0}".format(str(err)))
                raise err

            except smtplib.SMTPSenderRefused as err:
                # The server didn't accept the from_addr.
                self._logger.error("From address rejected\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
                self._logger.error("{0}".format(str(err)))
                raise err

            except smtplib.SMTPDataError as err:
                # The server replied with an unexpected error code (other than a refusal of a recipient).
                self._logger.error("SMTP Server Error\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
                self._logger.error("{0}".format(str(err)))
                raise err

            except Exception as err:
                self._logger.error("SMTP Unknown Error Sending Email\n{0}\n{1}\n".format(type(err),
                                                                                         traceback.format_exc()))
                raise err

            finally:
                smtp_email.quit()

        except Exception as err:
            self._logger.error("Error Sending Email\n{0}\n{1}\n".format(type(err), traceback.format_exc()))
            raise err
