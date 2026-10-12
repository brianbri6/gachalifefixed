public static function fromXML(param1:XML) : Color
{
   return Color(new Color().parseXML(param1));
}
