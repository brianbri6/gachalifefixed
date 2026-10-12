private function parseXML(param1:XML = null) : Color
{
   var _loc3_:XML = null;
   var _loc4_:String = null;
   var _loc5_:uint = 0;
   if(!param1)
   {
      return this;
   }
   var _loc2_:XML = param1.elements()[0];
   if(!_loc2_)
   {
      return this;
   }
   for each(_loc3_ in _loc2_.attributes())
   {
      _loc4_ = _loc3_.localName();
      if(_loc4_ == "tintColor")
      {
         _loc5_ = Number(_loc3_.toString()) as uint;
         this.tintColor = _loc5_;
      }
      else
      {
         this[_loc4_] = Number(_loc3_.toString());
      }
   }
   return this;
}
