# -*- coding:utf-8 -*-
#
# Copyright (C) 2011, 2012 Carlos Jenkins <carlos@jenkins.co.cr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Document Tree Manager for Nested.
"""

    def _previous(self, treestore, current):
        """Get the previous row on a TreeStore given an iter."""
        # Get the current iter position
        current_path = treestore.get_path(current)
        current_depth = treestore.iter_depth(current)
        # Check that the current iter is not the first child
        if current_path[current_depth] > 0:
            # Get the previous iter
            previous_path = list(current_path) # Tuples are inmutable :S
            previous_path[current_depth] = previous_path[current_depth] - 1
            previous = treestore.get_iter(tuple(previous_path))
            return previous
        else:
            return None


    def _change_custody(self, treestore, old, new):
        """Migrate all the children of one row to another row"""
        # Check if the old row has children
        if treestore.iter_has_child(old):
            # Get the first child
            old_child = treestore.iter_children(old)
            while old_child is not None:
                # Get current child data
                title, bloqued, text = treestore.get(old_child, 0, 1, 2)
                # Add child to the new parent
                new_child = treestore.append(new, [title, bloqued, text])
                # Check if this child has children
                self._change_custody(treestore, old_child, new_child)
                # Update index
                old_child = treestore.iter_next(old_child)


    def _path_depend_on_path(self, from_path, to_path):
        """Check if the remove of one path will affect another one and on what index"""
        i_from = len(from_path) - 1
        i_to = len(to_path) - 1

        if i_from > i_to:
            return -1
        elif from_path[i_from] > to_path[i_from]:
            return -1
        else: # Check that both paths have the same root
            i = i_from - 1
            while i > -1:
                if from_path[i] != to_path[i]:
                    return -1
                i -= 1
            return i_from


    def add_section(self, widget):
        """Callback to add a section to the document."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Append a new row
        if current is not None: # Some row is selected
            parent = self.editor_treestore.iter_parent(current)
            new = self.editor_treestore.insert_after(parent, current, [_('Untitled section'), False, ''])
            # Much better, but TreeView doesn't generate cursor-changed signal
            # with this option, so no sync_tree_fields() is called.
            #selection.select_iter(new)
            self.treeview.set_cursor(self.editor_treestore.get_path(new))
            self.modified(None, external=True)


    def remove_section(self, widget):
        """Callback to remove a section to the document."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Remove the row
        if current is not None: # Some row is selected
            # Check that we are not removing the only remaining section
            path = self.editor_treestore.get_path(current)
            next = self.editor_treestore.iter_next(current)
            if (path != self.root_path) or (next is not None):
                # Ask confirmation if section has something or childs
                # TODO
                still_valid = self.editor_treestore.remove(current)
                self.current_section = None # The current section has disappeared
                # Set the cursor if iter still valid
                if still_valid:
                    self.treeview.set_cursor(self.editor_treestore.get_path(current))
                else:
                    self.treeview.set_cursor(self.root_path)
                self.modified(None, external=True)


    def forward_section(self, widget):
        """Callback to move up one section on the document."""
         # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Move up a section
        if current is not None: # Some row is selected
            previous = self._previous(self.editor_treestore, current)
            if previous is not None: # Is not the first one
                self.editor_treestore.swap(current, previous)
                # Update current section
                self.current_section = self.treeview.get_cursor()[0]
                self.modified(None, external=True)


    def backward_section(self, widget):
        """Callback to move down one section on the document."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Move down a section
        if current is not None: # Some row is selected
            next = self.editor_treestore.iter_next(current)
            if next is not None: # Is not the last one
                self.editor_treestore.swap(current, next)
                # Update current section
                self.current_section = self.treeview.get_cursor()[0]
                self.modified(None, external=True)


    def downgrade_section(self, widget):
        """Move a document section down one level."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Make the current section child of the previous row
        if current is not None: # Some row is selected
            previous = self._previous(self.editor_treestore, current)
            if previous is not None:
                # Get current section data
                title, bloqued, text = self.editor_treestore.get(current, 0, 1, 2)
                # Add new section with previous as its parent
                new = self.editor_treestore.append(previous, [title, bloqued, text])
                # Migrate all the childrens of the old section
                self._change_custody(self.editor_treestore, current, new)
                # Remove old section
                self.editor_treestore.remove(current)
                # Expand parent
                self.treeview.expand_row(self.editor_treestore.get_path(previous), True)
                # Get the new path
                new_path = self.editor_treestore.get_path(new)
                # Update current section
                self.current_section = new_path
                #selection.select_iter(new) # See comments on add_section
                # Select the new row
                self.treeview.set_cursor(new_path)
                self.modified(None, external=True)


    def upgrade_section(self, widget):
        """Move a document section up one level."""
        # Get the TreeSelection object
        selection = self.treeview.get_selection()
        # Get the iter of the selected item
        current = selection.get_selected()[1]
        # Move the current row after his parent
        if current is not None: # Some row is selected
            parent = self.editor_treestore.iter_parent(current)
            if parent is not None:
                # Get current section data
                title, bloqued, text = self.editor_treestore.get(current, 0, 1, 2)
                # Insert the new row after his previous parent
                new = self.editor_treestore.insert_after(None, parent, [title, bloqued, text])
                # Migrate all the childrens of the old section
                self._change_custody(self.editor_treestore, current, new)
                # Remove old section
                self.editor_treestore.remove(current)
                # Expand the new node (in case it had children)
                self.treeview.expand_row(self.editor_treestore.get_path(new), True)
                # Get the new path
                new_path = self.editor_treestore.get_path(new)
                # Update current section
                self.current_section = new_path
                #selection.select_iter(new) # See comments on add_section
                # Select the new row
                self.treeview.set_cursor(new_path)
                self.modified(None, external=True)


    def drag_section_begin(self, treeview, drag_context):
        """Handles the movement of the current_section internal index to the new position of a row"""
        # Save content to the TreeStore, just in case
        title = self.title_entry.get_text()
        content = self.content_buffer.get_all_text()
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        model.set(iter, 0, title, 2, content)


    def drag_section_drop(self, treeview, drag_context, x, y, timestamp):
        """Handles the movement of the current_section internal index to the new position of a row"""
        # Get destination row
        row = treeview.get_dest_row_at_pos(x, y)
        if row is not None:
            to_path, how = row
        else: # This happens when the user drops the row to the end of the TreeView
            children = self.editor_treestore.iter_n_children(None)
            to_path = (children - 1, )
            how = gtk.TREE_VIEW_DROP_AFTER

        # Get the source row
        from_path = self.treeview.get_cursor()[0]

        # Check that the drop will change position of a row
        if from_path != to_path:

            # Find out if the move will affect final destination path
            compensation_index = self._path_depend_on_path(from_path, to_path)
            compensated_path = list(to_path)

            # Compensate
            if compensation_index >= 0:
                compensated_path[compensation_index] -= 1

            # Find where was put the row
            if how == gtk.TREE_VIEW_DROP_BEFORE:
                self.current_section = tuple(compensated_path)
            elif how == gtk.TREE_VIEW_DROP_AFTER:
                # Get the next position
                compensated_path[len(to_path) - 1] += 1
                self.current_section = tuple(compensated_path)
            else:
                #gtk.TREE_VIEW_DROP_INTO_OR_BEFORE & gtk.TREE_VIEW_DROP_INTO_OR_AFTER
                # Row will be the first child of the destination row (compensated)
                compensated_path.append(0)
                self.current_section = tuple(compensated_path)

            self.modified(None, external=True)

            # Debug
            #logger.debug('I guest the new position is: ' + str(self.current_section))


    def drag_section_end(self, treeview, drag_context):
        """Show and select the row just being dragged"""
        # Expand parent of the dragged element, if exist
        iter = self.editor_treestore.get_iter(self.current_section)
        parent = self.editor_treestore.iter_parent(iter)
        if parent is not None:
            treeview.expand_row(self.editor_treestore.get_path(parent), True)
        # Select the new row
        self.treeview.set_cursor(self.current_section)


