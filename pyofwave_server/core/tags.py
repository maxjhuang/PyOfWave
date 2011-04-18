"""
This file provides access to a simplified interface upon deltas and documents called "Tags".
"""
import delta, datasource

annotationOffsets = {
   "updateAttributes" : 1,
   "elementStart" : 1,
   "annotationsBoundary" : 1
}

class Tag(object):
   """Simplified document interface."""
   def __init__(self, doc, item, op = "retain"):
      #correct parameters
      if isinstance(doc, Tag): doc = doc._doc
      
      if isinstance(doc, str):
         item = datasource.Item(datasource.Item.OPEN_TAG, item)
         if op == "retain": op = "elementStart"
         
      if op == "elementStart": self._closeTag = True
      else self._closeTag = False
      
      self._doc = doc
      self._item = item
      self._delta = delta.Operation(op)

      #extract children
      self._content = []
      
      i = doc.items.index(self._item) + 1
      end = doc.items.index(self._item.end)
      while i < end:
         item = doc.items[i]
         self._content.append(Tag(doc, item))
         i = doc.items.index(item.end) + 1

   @property
   def _name(self): 
      """Returns the tag name/text of the tag, readonly."""
      return self._item.name

   #itterable properties
   def __len__(self):
      """Returns the number of direct children of the tag."""
      return len(self._content)

   def __getitem__(self, index):
      """Returns the child at specified index."""
      return self._content[i]

   def __setitem__(self, index, value):
      """Inserts (not replaces, use del for that) an object at index.
         Accepts Tag-like objects and strings.
         TODO: Correct processing to yield proper deltas."""
      if isinstance(value, str): value = Text(object)
      self.content[i] = value

   #psuedo-properties
   def __getattr__(self, attr):
      """Returns the appropriate annotation value."""
      return self._item.annotations[attr]

   def __setattr__(self, attr, value):
      """Edits delta to set the appropriate annotation. 
         :warning: This does note apply it until you call :ref:sendDelta. """
      #edit delta to set the attr
      index = self._delta.operation.__name__
      if index == "retain":
         self._delta = delta.Operation("updateAttributes", self._item.annotations)
         index = "updateAttributes"
      self._delta.args[index][attr] = value

    def __delattr__(self, attr):
       """Edits delta to remove an annotation.
           :warning: This does not apply it until you call :ref:sendDelta.""""
       opName = self._delta.operation.__name__
       #handle new tags appropriately
       if opName = "elementStart":
          del self._delta.args[1][attr]
          return
         
       #ensure delta is is a annotationsBoundary
       if opName != "annotationBoundary":
          #backup information
          annotations = self._delta.args[annotationOffset[opName]]

          #combine with existing annotations
          keys = set().union(set(annotations.keys()), set(self._item.annotations.keys()))

          ann = {}
          for key in keys: ann[key] = (self._item.annotations[key], annotations[key]) 

          self._delta = delta.Operation("annotationsBoundary", [], ann)
       #edit delta to delete the attr
       self._delta.args[0].append(attr)

   #delta creation
   def _contentdelta(self, deltas):
      """Generates the list of operations for :ref:sendDelta."""
      deltas.append(self._delta)
      for child in self._content: child._contentdelta(deltas)

   def sendDelta(self):
      """Sends a beta delta based on the changes to this object and it's children."""
      #create delta
      ops = []
      self._contentdelta(ops)

      #collapse retains
      fops = []
      curop = None
      for op in ops:
         if curop and op.operation.__name__ == curop.operation.__name__ == "retain":
            curop.args[0]++
         elif op.operation.__name__ == "retain":
            op.args[0] = 1
            fops.append(op)
            curop = op
         else:
            curop = op
            fops.append(op)
            
      delta = delta.Delta(*fops)
      
      delta.betaDeltaObservable.applyDelta(self._doc, delta)

class Text(object):
   """Represents textual changes. """
   def __init__(self, text):
      self.__delta = delta.Operation("charactors", text)

   def _contentdelta(self, deltas):
      deltas.appand(self.__delta)
