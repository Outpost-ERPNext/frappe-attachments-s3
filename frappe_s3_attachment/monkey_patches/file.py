# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.core.doctype.file.file import File

from frappe_s3_attachment.controller import S3Operations, s3_file_regex_match

_original_get_content = File.get_content


def get_content(self):
	"""
	Core File.get_content() treats file_url as a local disk path (see
	File.get_full_path() -> open()). For files uploaded via frappe_s3_attachment,
	file_url is either an /api/method/...generate_file URL (private) or an
	https://s3... URL (public), not a filesystem path, so core's implementation
	raises FileNotFoundError when called server-side (e.g. ERPNext's
	attached_file.get_content()). Fetch the bytes straight from S3 instead,
	using content_hash, which frappe_s3_attachment always sets to the S3 object
	key on upload (see controller.file_upload_to_s3).
	"""
	if self.is_folder:
		frappe.throw(_("Cannot get file contents of a Folder"))

	if self.get("content"):
		return _original_get_content(self)

	if self.file_url and self.content_hash and s3_file_regex_match(self.file_url):
		s3_object = S3Operations().read_file_from_s3(self.content_hash)
		self._content = s3_object["Body"].read()
		try:
			self._content = self._content.decode()
		except UnicodeDecodeError:
			pass
		return self._content

	return _original_get_content(self)


File.get_content = get_content
